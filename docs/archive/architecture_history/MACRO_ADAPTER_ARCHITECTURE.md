# Document Status

Status:
ARCHIVED

Reason:
Historical record only

Superseded by:
See docs/ARCHITECTURE_FREEZE_V2.md (current constitution)

Original purpose:
See docs/DOCUMENTATION_INVENTORY_REPORT.md

---

# ResearchOS Macro Intelligence Layer — Source Adapter Architecture

**Version:** 1.0.0-frozen
**Date:** 2026-08-03
**Status:** ARCHITECTURALLY FROZEN — Ready for Implementation
**Classification:** Internal — Quantitative Platform

---

## Table of Contents

1. [Adapter Framework Architecture](#1-adapter-framework-architecture)
2. [Base Adapter Interface](#2-base-adapter-interface)
3. [Adapter Registry](#3-adapter-registry)
4. [Retry & Rate Limit Policy](#4-retry--rate-limit-policy)
5. [Failure Isolation](#5-failure-isolation)
6. [FRED Adapter Contract](#6-fred-adapter-contract)
7. [BLS Adapter Contract](#7-bls-adapter-contract)
8. [Treasury Adapter Contract](#8-treasury-adapter-contract)
9. [Federal Reserve Adapter Contract](#9-federal-reserve-adapter-contract)
10. [CFTC Adapter Contract](#10-cftc-adapter-contract)
11. [CBOE Adapter Contract](#11-cboe-adapter-contract)
12. [Adapter Lifecycle](#12-adapter-lifecycle)
13. [Health Monitoring](#13-health-monitoring)
14. [Testing Strategy](#14-testing-strategy)

---

## 1. Adapter Framework Architecture

### 1.1 Design Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Adapter Registry                              │  │
│  │  (Source ID → Adapter mapping, lifecycle management)       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│        ┌─────────────────────┼─────────────────────┐             │
│        │                     │                     │             │
│        ▼                     ▼                     ▼             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      │
│  │  FRED       │      │  BLS        │      │  Treasury   │      │
│  │  Adapter    │      │  Adapter    │      │  Adapter    │      │
│  └──────┬──────┘      └──────┬──────┘      └──────┬──────┘      │
│         │                    │                    │              │
│         └────────────────────┴────────────────────┘              │
│                              │                                   │
│                              ▼                                   │
│              ┌─────────────────────────────────┐                 │
│              │         Base Adapter            │                 │
│              │   (Abstract interface +         │                 │
│              │    common retry/rate limit/     │                 │
│              │    failure isolation logic)     │                 │
│              └─────────────────────────────────┘                 │
│                              │                                   │
│        ┌─────────────────────┼─────────────────────┐             │
│        │                     │                     │              │
│        ▼                     ▼                     ▼              │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      │
│  │  Fed       │      │  CFTC       │      │  CBOE       │      │
│  │  Adapter   │      │  Adapter    │      │  Adapter    │      │
│  └─────────────┘      └─────────────┘      └─────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Normalization  │
                    │     Layer       │
                    └─────────────────┘
```

### 1.2 Adapter Layer Responsibilities

| Responsibility | Description |
|---------------|-------------|
| **Source Translation** | Convert heterogeneous source formats to common RawRecord schema |
| **Error Handling** | Isolated error handling per source; failures don't cascade |
| **Rate Limiting** | Respect source rate limits with exponential backoff |
| **Retry Logic** | Configurable retry with exponential backoff and jitter |
| **Health Monitoring** | Track source health status and alert on degradation |
| **Credential Management** | Secure credential storage and rotation |
| **Caching** | Cache recent responses to reduce API calls |
| **Audit Logging** | Log all adapter operations for compliance |

### 1.3 Adapter Interface Hierarchy

```
BaseAdapter (ABC)
    │
    ├── Abstract methods:
    │   ├── adapt(raw_bytes) -> list[RawRecord]
    │   ├── parse_error(response) -> AdapterError | None
    │   ├── health_check() -> bool
    │   └── get_supported_series() -> list[str]
    │
    ├── Common implementations:
    │   ├── retry_with_backoff()
    │   ├── check_rate_limit()
    │   ├── cache_response()
    │   └── log_operation()
    │
    └── Concrete adapters:
        ├── FREDAdapter
        ├── BLSAdapter
        ├── TreasuryAdapter
        ├── FederalReserveAdapter
        ├── CFTCAdapter
        └── CBOEAdapter
```

---

## 2. Base Adapter Interface

**Version:** `adapter/base/v1`
**Module:** `macro_intelligence.adapters.base`
**Status:** Frozen

### 2.1 BaseAdapter Abstract Class

```python
class BaseAdapter(ABC):
    """
    Abstract base class for all macro data source adapters.
    
    All concrete adapters MUST implement:
    - SOURCE_TYPE: str (class attribute)
    - adapt(): RawRecord -> NormalizedSeries
    - parse_error(): Response -> AdapterError | None
    - health_check(): bool
    - get_supported_series(): list[str]
    
    Common functionality (retry, rate limiting, caching) is provided
    by the base class implementation.
    """
    
    # Class-level constants
    SOURCE_TYPE: str = NotImplemented
    ADAPTER_VERSION: str = "v1"
    DEFAULT_TIMEOUT: int = 30  # seconds
    DEFAULT_RETRIES: int = 3
    DEFAULT_BACKOFF_FACTOR: float = 2.0
    DEFAULT_BACKOFF_MAX: timedelta = timedelta(minutes=5)
    
    def __init__(
        self,
        config: SourceConfig,
        cache: ResponseCache | None = None,
        rate_limiter: RateLimiter | None = None,
    ):
        self.config = config
        self.cache = cache or ResponseCache()
        self.rate_limiter = rate_limiter or RateLimiter()
        self._health_status = HealthStatus.HEALTHY
        self._last_success: datetime | None = None
        self._last_error: str | None = None
        self._consecutive_failures: int = 0
    
    # =====================================================================
    # ABSTRACT METHODS (Must be implemented by concrete adapters)
    # =====================================================================
    
    @abstractmethod
    def adapt(self, raw_bytes: bytes, source_format: str = "json") -> list[RawRecord]:
        """
        Transform raw source data into standardized RawRecord objects.
        
        Args:
            raw_bytes: Raw response bytes from source
            source_format: Format of raw data (json, xml, csv, html)
        
        Returns:
            List of RawRecord objects
        
        Raises:
            AdaptError: If transformation fails
        """
        ...
    
    @abstractmethod
    def parse_error(self, response: dict | bytes) -> AdapterError | None:
        """
        Parse error responses from source API.
        
        Args:
            response: Error response from source
        
        Returns:
            AdapterError if response contains error, None otherwise
        """
        ...
    
    @abstractmethod
    def health_check(self) -> HealthResult:
        """
        Perform health check on source connectivity.
        
        Returns:
            HealthResult with status and diagnostics
        """
        ...
    
    @abstractmethod
    def get_supported_series(self) -> list[str]:
        """
        Return list of series IDs supported by this adapter.
        
        Returns:
            List of series_id strings
        """
        ...
    
    # =====================================================================
    # CONCRETE METHODS (Common functionality)
    # =====================================================================
    
    def fetch(
        self,
        endpoint: str,
        params: dict | None = None,
        timeout: int | None = None,
    ) -> bytes:
        """
        Fetch data from source with retry and rate limiting.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            timeout: Request timeout in seconds
        
        Returns:
            Response bytes
        
        Raises:
            SourceFetchError: If fetch fails after all retries
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        # Check rate limit
        self.rate_limiter.acquire(self.SOURCE_TYPE)
        
        # Check cache first
        cache_key = self._generate_cache_key(endpoint, params)
        cached = self.cache.get(cache_key)
        if cached and not self._is_cache_expired(cached, endpoint):
            return cached.data
        
        # Fetch with retry
        last_error = None
        for attempt in range(1, self.DEFAULT_RETRIES + 1):
            try:
                response = self._do_fetch(endpoint, params, timeout)
                
                # Check for error
                error = self.parse_error(response)
                if error:
                    raise SourceFetchError(
                        source=self.SOURCE_TYPE,
                        error=error,
                        attempt=attempt,
                    )
                
                # Success
                self._record_success()
                self.cache.set(cache_key, ResponseCacheEntry(
                    data=response,
                    fetched_at=datetime.utcnow(),
                    endpoint=endpoint,
                    params=params,
                ))
                return response
                
            except SourceFetchError as e:
                last_error = e
                if attempt < self.DEFAULT_RETRIES:
                    wait_time = self._calculate_backoff(attempt)
                    time.sleep(wait_time)
                else:
                    self._record_failure(str(e))
        
        raise SourceFetchError(
            source=self.SOURCE_TYPE,
            error=last_error.error if last_error else None,
            attempt=self.DEFAULT_RETRIES,
        )
    
    def _do_fetch(
        self,
        endpoint: str,
        params: dict | None,
        timeout: int,
    ) -> bytes:
        """Perform actual HTTP fetch (to be implemented by concrete adapters)."""
        ...
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter."""
        base_delay = min(
            self.DEFAULT_BACKOFF_FACTOR ** (attempt - 1),
            self.DEFAULT_BACKOFF_MAX.total_seconds(),
        )
        jitter = random.uniform(0, base_delay * 0.1)
        return base_delay + jitter
    
    def _record_success(self) -> None:
        """Record successful fetch."""
        self._last_success = datetime.utcnow()
        self._consecutive_failures = 0
        self._health_status = HealthStatus.HEALTHY
    
    def _record_failure(self, error: str) -> None:
        """Record failed fetch."""
        self._last_error = error
        self._consecutive_failures += 1
        if self._consecutive_failures >= 5:
            self._health_status = HealthStatus.DEGRADED
        elif self._consecutive_failures >= 10:
            self._health_status = HealthStatus.UNHEALTHY
    
    def _generate_cache_key(self, endpoint: str, params: dict | None) -> str:
        """Generate deterministic cache key."""
        import hashlib
        key_data = f"{self.SOURCE_TYPE}:{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def _is_cache_expired(self, entry: ResponseCacheEntry, endpoint: str) -> bool:
        """Check if cached response is expired based on endpoint."""
        expiration_rules = {
            "federal/fomc/meetings.json": timedelta(hours=1),
            "series/{id}/observations.json": timedelta(hours=6),
        }
        expiration = expiration_rules.get(endpoint, timedelta(minutes=30))
        return datetime.utcnow() - entry.fetched_at > expiration
```

### 2.2 Data Classes

```python
@dataclass(frozen=True)
class RawRecord:
    """Standardized raw record from source adapter."""
    source_id: str                          # e.g., "fred", "bls"
    raw_key: str                            # e.g., "DXY", "UNRATE"
    received_at: datetime                   # When record was received
    raw_payload: dict                       # Source-native JSON/dict
    source_url: str | None = None           # Original API URL
    format: str = "json"                    # Original format
    content_type: str = "application/json"  # MIME type

@dataclass(frozen=True)
class AdapterError:
    """Standardized error from adapter."""
    error_type: ErrorType                   # TIMEOUT, RATE_LIMIT, AUTH_ERROR, etc.
    message: str
    source_status_code: int | None = None
    source_error_code: str | None = None
    retry_after: timedelta | None = None    # Suggested retry delay

@dataclass(frozen=True)
class HealthResult:
    """Health check result."""
    status: HealthStatus                    # HEALTHY, DEGRADED, UNHEALTHY
    last_check: datetime
    last_success: datetime | None
    last_error: str | None
    response_time_ms: float | None
    consecutive_failures: int
    details: dict = field(default_factory=dict)

@dataclass(frozen=True)
class ResponseCacheEntry:
    """Cached API response."""
    data: bytes
    fetched_at: datetime
    endpoint: str
    params: dict | None
    ttl: timedelta = timedelta(hours=1)
```

### 2.3 Enums

```python
class ErrorType(Enum):
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    AUTH_ERROR = "auth_error"
    NOT_FOUND = "not_found"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    INVALID_RESPONSE = "invalid_response"
    NETWORK_ERROR = "network_error"

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class SourceType(Enum):
    FRED = "fred"
    BLS = "bls"
    TREASURY = "treasury"
    FEDERAL_RESERVE = "federal_reserve"
    CFTC = "cftc"
    CBOE = "cboe"
    ISM = "ism"
    WGC = "wgc"
```

---

## 3. Adapter Registry

**Version:** `registry/v1`
**Module:** `macro_intelligence.adapters.registry`
**Status:** Frozen

### 3.1 Registry Interface

```python
class AdapterRegistry:
    """
    Central registry for all source adapters.
    
    Responsibilities:
    - Maintain mapping of source_id to adapter instance
    - Provide adapter lookup by source_type
    - Manage adapter lifecycle (init, health check, shutdown)
    - Aggregate health status across all adapters
    """
    
    def __init__(self):
        self._adapters: dict[str, BaseAdapter] = {}
        self._lock = threading.RLock()
    
    def register(self, adapter: BaseAdapter) -> None:
        """
        Register an adapter instance.
        
        Args:
            adapter: Concrete adapter implementation
        """
        with self._lock:
            if adapter.SOURCE_TYPE in self._adapters:
                raise RegistryError(
                    f"Adapter for source '{adapter.SOURCE_TYPE}' already registered"
                )
            self._adapters[adapter.SOURCE_TYPE] = adapter
    
    def get(self, source_type: str) -> BaseAdapter:
        """
        Get adapter by source type.
        
        Args:
            source_type: Source type string (e.g., "fred", "bls")
        
        Returns:
            Adapter instance
        
        Raises:
            RegistryError: If adapter not found
        """
        with self._lock:
            adapter = self._adapters.get(source_type)
            if not adapter:
                raise RegistryError(f"No adapter registered for source '{source_type}'")
            return adapter
    
    def get_all(self) -> dict[str, BaseAdapter]:
        """
        Get all registered adapters.
        
        Returns:
            Dict mapping source_type to adapter instance
        """
        with self._lock:
            return dict(self._adapters)
    
    def get_health_summary(self) -> dict[str, HealthResult]:
        """
        Get health status for all adapters.
        
        Returns:
            Dict mapping source_type to HealthResult
        """
        with self._lock:
            return {
                source_type: adapter.health_check()
                for source_type, adapter in self._adapters.items()
            }
    
    def is_healthy(self, source_type: str) -> bool:
        """
        Check if adapter is healthy.
        
        Args:
            source_type: Source type string
        
        Returns:
            True if adapter health status is HEALTHY
        """
        with self._lock:
            adapter = self._adapters.get(source_type)
            if not adapter:
                return False
            return adapter._health_status == HealthStatus.HEALTHY
    
    def get_supported_series(self) -> dict[str, list[str]]:
        """
        Get all supported series across all adapters.
        
        Returns:
            Dict mapping source_type to list of series_ids
        """
        with self._lock:
            return {
                source_type: adapter.get_supported_series()
                for source_type, adapter in self._adapters.items()
            }
```

### 3.2 Registry Initialization

```python
def initialize_registry(config: SourceConfig) -> AdapterRegistry:
    """
    Initialize adapter registry with all configured adapters.
    
    Args:
        config: Source configuration with credentials and settings
    
    Returns:
        Initialized AdapterRegistry
    """
    registry = AdapterRegistry()
    
    # Register all concrete adapters
    registry.register(FREDAdapter(config.fred))
    registry.register(BLSAdapter(config.bls))
    registry.register(TreasuryAdapter(config.treasury))
    registry.register(FederalReserveAdapter(config.federal_reserve))
    registry.register(CFTCAdapter(config.cftc))
    registry.register(CBOEAdapter(config.cboe))
    
    # Log initialization
    logger.info(f"Registered {len(registry._adapters)} adapters")
    
    return registry
```

---

## 4. Retry & Rate Limit Policy

### 4.1 Retry Policy

```python
@dataclass(frozen=True)
class RetryPolicy:
    """
    Configurable retry policy for adapter operations.
    """
    max_retries: int = 3
    backoff_factor: float = 2.0
    backoff_max: timedelta = timedelta(minutes=5)
    jitter: bool = True
    retryable_errors: list[ErrorType] = field(default_factory=lambda: [
        ErrorType.TIMEOUT,
        ErrorType.RATE_LIMIT,
        ErrorType.SERVER_ERROR,
        ErrorType.NETWORK_ERROR,
    ])

class RetryExecutor:
    """
    Executes operations with retry logic.
    """
    
    def __init__(self, policy: RetryPolicy):
        self.policy = policy
    
    def execute(self, operation: callable, *args, **kwargs) -> Any:
        """
        Execute operation with retry logic.
        
        Args:
            operation: Callable to execute
            *args, **kwargs: Arguments to pass
        
        Returns:
            Operation result
        
        Raises:
            FinalRetryError: If all retries exhausted
        """
        last_error = None
        
        for attempt in range(1, self.policy.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            
            except Exception as e:
                last_error = e
                
                # Check if error is retryable
                if not self._is_retryable(e):
                    raise
                
                # Check if we have retries left
                if attempt >= self.policy.max_retries:
                    raise FinalRetryError(
                        operation=operation.__name__,
                        attempt=attempt,
                        error=e,
                    )
                
                # Calculate backoff
                wait_time = self._calculate_backoff(attempt)
                logger.warning(
                    f"Attempt {attempt}/{self.policy.max_retries} failed for "
                    f"{operation.__name__}: {e}. Retrying in {wait_time}s"
                )
                time.sleep(wait_time)
        
        raise FinalRetryError(
            operation=operation.__name__,
            attempt=self.policy.max_retries,
            error=last_error,
        )
    
    def _is_retryable(self, error: Exception) -> bool:
        """Check if error is retryable."""
        if isinstance(error, SourceFetchError):
            return error.error.error_type in self.policy.retryable_errors
        return False
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with optional jitter."""
        base_delay = min(
            self.policy.backoff_factor ** (attempt - 1),
            self.policy.backoff_max.total_seconds(),
        )
        if self.policy.jitter:
            jitter = random.uniform(0, base_delay * 0.1)
            return base_delay + jitter
        return base_delay
```

### 4.2 Rate Limiter

```python
class RateLimiter:
    """
    Token bucket rate limiter for API sources.
    """
    
    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()
    
    def acquire(self, source_type: str, tokens: int = 1) -> None:
        """
        Acquire tokens from rate limit bucket.
        
        Args:
            source_type: Source type identifier
            tokens: Number of tokens to acquire
        
        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        with self._lock:
            bucket = self._get_or_create_bucket(source_type)
            bucket.acquire(tokens)
    
    def _get_or_create_bucket(self, source_type: str) -> TokenBucket:
        """Get or create rate limit bucket for source."""
        if source_type not in self._buckets:
            # Default rate limits per source
            default_limits = {
                "fred": RateLimitConfig(requests_per_minute=120, burst=10),
                "bls": RateLimitConfig(requests_per_minute=50, burst=5),
                "treasury": RateLimitConfig(requests_per_minute=100, burst=10),
                "cftc": RateLimitConfig(requests_per_minute=100, burst=10),
                "cboe": RateLimitConfig(requests_per_minute=30, burst=5),
            }
            config = default_limits.get(source_type, RateLimitConfig())
            self._buckets[source_type] = TokenBucket(config)
        return self._buckets[source_type]

@dataclass(frozen=True)
class RateLimitConfig:
    """Configuration for rate limit bucket."""
    requests_per_minute: int = 60
    burst: int = 10

class TokenBucket:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._tokens = config.burst
        self._last_refill = datetime.utcnow()
    
    def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens from bucket.
        
        Raises:
            RateLimitExceeded: If insufficient tokens
        """
        self._refill()
        
        if self._tokens < tokens:
            raise RateLimitExceeded(
                source=self.config.requests_per_minute,
                retry_after=timedelta(seconds=1),
            )
        
        self._tokens -= tokens
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = datetime.utcnow()
        elapsed = (now - self._last_refill).total_seconds()
        refill_rate = self.config.requests_per_minute / 60.0
        self._tokens = min(
            self.config.burst,
            self._tokens + elapsed * refill_rate,
        )
        self._last_refill = now
```

---

## 5. Failure Isolation

### 5.1 Isolation Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    FAILURE ISOLATION LAYER                       │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  FRED       │    │  BLS        │    │  Treasury   │         │
│  │  Circuit    │    │  Circuit    │    │  Circuit    │         │
│  │  Breaker    │    │  Breaker    │    │  Breaker    │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                   │
│                            ▼                                   │
│              ┌─────────────────────────────────┐                 │
│              │        Failure Aggregator        │                 │
│              │   (Logs, alerts, recovery)       │                 │
│              └─────────────────────────────────┘                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Circuit Breaker Pattern

```python
class CircuitBreaker:
    """
    Circuit breaker for failure isolation.
    
    States:
    - CLOSED: Normal operation
    - OPEN: Failures detected, requests blocked
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(
        self,
        source_type: str,
        failure_threshold: int = 5,
        recovery_timeout: timedelta = timedelta(minutes=5),
        half_open_max_calls: int = 3,
    ):
        self.source_type = source_type
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: datetime | None = None
        self._half_open_calls = 0
        self._lock = threading.Lock()
    
    def execute(self, operation: callable, *args, **kwargs) -> Any:
        """
        Execute operation with circuit breaker protection.
        
        Raises:
            CircuitOpenError: If circuit is open
        """
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                else:
                    raise CircuitOpenError(
                        source=self.source_type,
                        retry_after=self._get_retry_after(),
                    )
            
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitOpenError(
                        source=self.source_type,
                        message="Half-open circuit at max calls",
                    )
                self._half_open_calls += 1
        
        try:
            result = operation(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise
    
    def _on_success(self) -> None:
        """Handle successful operation."""
        with self._lock:
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
    
    def _on_failure(self, error: Exception) -> None:
        """Handle failed operation."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.utcnow()
            
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.error(
                    f"Circuit OPEN for {self.source_type} after "
                    f"{self._failure_count} failures"
                )
    
    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed for recovery attempt."""
        if not self._last_failure_time:
            return False
        return datetime.utcnow() - self._last_failure_time >= self.recovery_timeout
    
    def _get_retry_after(self) -> timedelta:
        """Get suggested retry delay."""
        return self.recovery_timeout - (datetime.utcnow() - self._last_failure_time)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
```

### 5.3 Failure Aggregator

```python
class FailureAggregator:
    """
    Aggregates failures across all adapters for alerting and monitoring.
    """
    
    def __init__(self):
        self._failures: dict[str, list[FailureRecord]] = {}
        self._lock = threading.Lock()
    
    def record_failure(self, source_type: str, error: Exception) -> None:
        """Record a failure for an adapter."""
        with self._lock:
            if source_type not in self._failures:
                self._failures[source_type] = []
            
            self._failures[source_type].append(FailureRecord(
                source_type=source_type,
                error=str(error),
                timestamp=datetime.utcnow(),
            ))
            
            # Keep only last 100 failures per source
            self._failures[source_type] = self._failures[source_type][-100:]
            
            # Alert on critical failures
            if self._is_critical_failure(source_type):
                self._alert(source_type, error)
    
    def _is_critical_failure(self, source_type: str) -> bool:
        """Check if failure pattern is critical."""
        failures = self._failures.get(source_type, [])
        if len(failures) < 5:
            return False
        
        # Check for rapid failures (5+ in last minute)
        recent = [
            f for f in failures
            if datetime.utcnow() - f.timestamp < timedelta(minutes=1)
        ]
        return len(recent) >= 5
    
    def _alert(self, source_type: str, error: Exception) -> None:
        """Send alert for critical failure pattern."""
        logger.critical(
            f"CRITICAL: {source_type} experiencing rapid failures: {error}"
        )
        # Integration with alerting system would go here
    
    def get_failure_stats(self, source_type: str) -> dict:
        """Get failure statistics for a source."""
        with self._lock:
            failures = self._failures.get(source_type, [])
            return {
                "total_failures": len(failures),
                "last_failure": failures[-1].timestamp if failures else None,
                "failure_rate_1h": self._calculate_rate(failures, timedelta(hours=1)),
                "failure_rate_24h": self._calculate_rate(failures, timedelta(hours=24)),
            }
    
    def _calculate_rate(self, failures: list[FailureRecord], window: timedelta) -> float:
        """Calculate failure rate over time window."""
        cutoff = datetime.utcnow() - window
        recent = [f for f in failures if f.timestamp >= cutoff]
        return len(recent) / window.total_seconds() * 3600  # failures per hour
```

---

## 6. FRED Adapter Contract

**Version:** `adapter/fred/v1`
**Module:** `macro_intelligence.adapters.fred`
**Status:** Frozen

### 6.1 FRED Adapter Overview

| Property | Value |
|----------|-------|
| Source Type | `fred` |
| API Base URL | `https://fred.stlouisfed.org/graph/fredgraph` |
| Rate Limit | 120 requests/minute (free tier) |
| Authentication | API key required |
| Data Format | JSON |
| Supported Series | 15+ macro series |

### 6.2 FRED Adapter Interface

```python
class FREDAdapter(BaseAdapter):
    """
    Adapter for Federal Reserve Economic Data (FRED) API.
    
    Supported series:
    - DXY: US Dollar Index
    - US2Y, US5Y, US10Y, US30Y: Treasury yields
    - CPI, CPIAUCSL: Consumer Price Index
    - PPI, PPIACO: Producer Price Index
    - PCE, PCECB: Personal Consumption Expenditures
    - UNRATE: Unemployment Rate
    - GDP: Gross Domestic Product
    """
    
    SOURCE_TYPE = "fred"
    API_BASE = "https://api.stlouisfed.org/fred"
    
    # FRED-specific series IDs
    SERIES_MAP = {
        "DXY": "DTWEXBGS",           # Trade-weighted dollar index
        "US2Y": "GS2",                # 2-Year Treasury yield
        "US5Y": "GS5",                # 5-Year Treasury yield
        "US10Y": "GS10",              # 10-Year Treasury yield
        "US30Y": "GS30",              # 30-Year Treasury yield
        "CPI": "CPIAUCSL",            # Consumer Price Index
        "CPI_CORE": "CPILFESL",       # Core CPI
        "PPI": "PPIACO",              # Producer Price Index
        "PPI_CORE": "PPICORE",        # Core PPI
        "PCE": "PCECB",               # Personal Consumption Expenditures
        "PCE_CORE": "PCEPILFE",       # Core PCE
        "UNRATE": "UNRATE",           # Unemployment Rate
        "GDP": "GDP",                 # Gross Domestic Product
        "REAL_10Y": "DFII10",         # 10-Year Breakeven (for real yield)
    }
    
    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self.api_key = config.credentials.get("api_key", "")
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "ResearchOS-Macro-Intelligence-Layer/1.0"
        })
    
    def adapt(self, raw_bytes: bytes, source_format: str = "json") -> list[RawRecord]:
        """
        Transform FRED API response into RawRecord objects.
        
        Args:
            raw_bytes: FRED API JSON response
            source_format: "json" (default)
        
        Returns:
            List of RawRecord objects
        """
        data = json.loads(raw_bytes.decode("utf-8"))
        records = []
        
        for obs in data.get("observations", []):
            records.append(RawRecord(
                source_id=self.SOURCE_TYPE,
                raw_key=data.get("series_id", "UNKNOWN"),
                received_at=datetime.utcnow(),
                raw_payload={
                    "date": obs.get("date"),
                    "value": obs.get("value"),
                    "footnote": obs.get("footnote"),
                },
                source_url=self._build_url(data.get("series_id")),
            ))
        
        return records
    
    def parse_error(self, response: dict | bytes) -> AdapterError | None:
        """
        Parse FRED API error response.
        
        Args:
            response: FRED API error response
        
        Returns:
            AdapterError if error, None otherwise
        """
        if isinstance(response, bytes):
            response = json.loads(response.decode("utf-8"))
        
        error_code = response.get("error_code")
        error_message = response.get("error_message")
        
        if error_code:
            if error_code == 100:
                return AdapterError(
                    error_type=ErrorType.AUTH_ERROR,
                    message=error_message,
                    source_status_code=401,
                )
            elif error_code == 200:
                return AdapterError(
                    error_type=ErrorType.RATE_LIMIT,
                    message=error_message,
                    source_status_code=429,
                    retry_after=timedelta(seconds=1),
                )
            else:
                return AdapterError(
                    error_type=ErrorType.CLIENT_ERROR,
                    message=error_message,
                    source_status_code=400,
                )
        
        return None
    
    def health_check(self) -> HealthResult:
        """
        Perform FRED API health check.
        
        Returns:
            HealthResult with status
        """
        start = datetime.utcnow()
        try:
            response = self._session.get(
                f"{self.API_BASE}/series/observations",
                params={"series_id": "GDP", "api_key": self.api_key, "limit": 1},
                timeout=10,
            )
            response_time = (datetime.utcnow() - start).total_seconds() * 1000
            
            if response.status_code == 200:
                return HealthResult(
                    status=HealthStatus.HEALTHY,
                    last_check=datetime.utcnow(),
                    last_success=datetime.utcnow(),
                    last_error=None,
                    response_time_ms=response_time,
                    consecutive_failures=0,
                )
            else:
                return HealthResult(
                    status=HealthStatus.DEGRADED,
                    last_check=datetime.utcnow(),
                    last_success=self._last_success,
                    last_error=f"HTTP {response.status_code}",
                    response_time_ms=response_time,
                    consecutive_failures=self._consecutive_failures,
                )
        except Exception as e:
            return HealthResult(
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow(),
                last_success=self._last_success,
                last_error=str(e),
                response_time_ms=(datetime.utcnow() - start).total_seconds() * 1000,
                consecutive_failures=self._consecutive_failures + 1,
            )
    
    def get_supported_series(self) -> list[str]:
        """Return list of FRED-supported series IDs."""
        return list(self.SERIES_MAP.keys())
    
    def fetch_series(self, series_id: str, start_date: date, end_date: date) -> bytes:
        """
        Fetch series observations from FRED.
        
        Args:
            series_id: FRED series ID (e.g., "GS10")
            start_date: Start date for observations
            end_date: End date for observations
        
        Returns:
            Raw API response bytes
        """
        fred_series_id = self.SERIES_MAP.get(series_id, series_id)
        params = {
            "series_id": fred_series_id,
            "api_key": self.api_key,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "sort_order": "asc",
            "limit": 10000,
        }
        return self.fetch("/series/observations", params)
    
    def _build_url(self, series_id: str) -> str:
        """Build FRED API URL for series."""
        return f"{self.API_BASE}/series/observations?series_id={series_id}&api_key={self.api_key}"
```

---

## 7. BLS Adapter Contract

**Version:** `adapter/bls/v1`
**Module:** `macro_intelligence.adapters.bls`
**Status:** Frozen

### 7.1 BLS Adapter Overview

| Property | Value |
|----------|-------|
| Source Type | `bls` |
| API Base URL | `https://api.bls.gov/publicAPI/v2` |
| Rate Limit | 50 requests/minute |
| Authentication | API key required |
| Data Format | JSON |
| Supported Series | CPI, PPI, Unemployment, JOLTS |

### 7.2 BLS Adapter Interface

```python
class BLSAdapter(BaseAdapter):
    """
    Adapter for Bureau of Labor Statistics (BLS) API.
    
    Supported series:
    - CPI_YOY, CPI_CORE_YOY, CPI_MOM: Consumer Price Index
    - PPI_YOY, PPI_CORE_YOY: Producer Price Index
    - UNRATE: Unemployment Rate
    - NFP_CHANGE: Non-Farm Payrolls
    - JOLTS_TOTAL, JOLTS_HIRINGS, JOLTS_SEPARATIONS: JOLTS data
    """
    
    SOURCE_TYPE = "bls"
    API_BASE = "https://api.bls.gov/publicAPI/v2"
    
    # BLS series IDs
    SERIES_MAP = {
        "CPI_YOY": "CUSR0000SA0",
        "CPI_CORE_YOY": "CUUR0000SA0",
        "PPI_YOY": "WPUFFE",
        "PPI_CORE_YOY": "WPPTFFE",
        "UNRATE": "LNS14000000",
        "NFP": "CES0000000001",
        "JOLTS_TOTAL": "JTSJOLTS",
        "JOLTS_HIRINGS": "JTSJOLTS",  # Requires separate endpoint
        "JOLTS_SEPARATIONS": "JTSJOLTS",  # Requires separate endpoint
    }
    
    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self.api_key = config.credentials.get("api_key", "")
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "ResearchOS-Macro-Intelligence-Layer/1.0"
        })
    
    def adapt(self, raw_bytes: bytes, source_format: str = "json") -> list[RawRecord]:
        """
        Transform BLS API response into RawRecord objects.
        """
        data = json.loads(raw_bytes.decode("utf-8"))
        records = []
        
        for series in data.get("Results", {}).get("series", []):
            for obs in series.get("observations", []):
                if not obs.get("value"):
                    continue
                
                records.append(RawRecord(
                    source_id=self.SOURCE_TYPE,
                    raw_key=series.get("seriesID"),
                    received_at=datetime.utcnow(),
                    raw_payload={
                        "year": obs.get("year"),
                        "period": obs.get("period"),
                        "periodName": obs.get("periodName"),
                        "value": obs.get("value"),
                        "footnote": obs.get("footnote"),
                    },
                    source_url=self._build_url(series.get("seriesID")),
                ))
        
        return records
    
    def parse_error(self, response: dict | bytes) -> AdapterError | None:
        """Parse BLS API error response."""
        if isinstance(response, bytes):
            response = json.loads(response.decode("utf-8"))
        
        status_code = response.get("status")
        message = response.get("message")
        
        if status_code != "REQUEST_SUCCEEDED":
            if status_code == "INVALID_KEY":
                return AdapterError(
                    error_type=ErrorType.AUTH_ERROR,
                    message=message,
                    source_status_code=401,
                )
            elif status_code == "RATE_LIMIT_EXCEEDED":
                return AdapterError(
                    error_type=ErrorType.RATE_LIMIT,
                    message=message,
                    source_status_code=429,
                    retry_after=timedelta(minutes=1),
                )
            else:
                return AdapterError(
                    error_type=ErrorType.CLIENT_ERROR,
                    message=message,
                    source_status_code=400,
                )
        
        return None
    
    def health_check(self) -> HealthResult:
        """Perform BLS API health check."""
        start = datetime.utcnow()
        try:
            response = self._session.post(
                f"{self.API_BASE}/observations/",
                json={
                    "validation": False,
                    "catalog": False,
                    "apikey": self.api_key,
                    "seriesid": ["LNS14000000"],
                    "startyear": 2026,
                    "endyear": 2026,
                },
                timeout=10,
            )
            response_time = (datetime.utcnow() - start).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                if data.get("Results", {}).get("series"):
                    return HealthResult(
                        status=HealthStatus.HEALTHY,
                        last_check=datetime.utcnow(),
                        last_success=datetime.utcnow(),
                        last_error=None,
                        response_time_ms=response_time,
                        consecutive_failures=0,
                    )
            
            return HealthResult(
                status=HealthStatus.DEGRADED,
                last_check=datetime.utcnow(),
                last_success=self._last_success,
                last_error=f"HTTP {response.status_code}",
                response_time_ms=response_time,
                consecutive_failures=self._consecutive_failures,
            )
        except Exception as e:
            return HealthResult(
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow(),
                last_success=self._last_success,
                last_error=str(e),
                response_time_ms=(datetime.utcnow() - start).total_seconds() * 1000,
                consecutive_failures=self._consecutive_failures + 1,
            )
    
    def get_supported_series(self) -> list[str]:
        """Return list of BLS-supported series IDs."""
        return list(self.SERIES_MAP.keys())
    
    def fetch_cpi(self, year: int) -> bytes:
        """Fetch CPI data for specific year."""
        return self.fetch("/observations/", {
            "validation": False,
            "catalog": False,
            "apikey": self.api_key,
            "seriesid": ["CUSR0000SA0", "CUUR0000SA0"],
            "startyear": year,
            "endyear": year,
        })
    
    def fetch_unemployment(self, year: int) -> bytes:
        """Fetch unemployment data for specific year."""
        return self.fetch("/observations/", {
            "validation": False,
            "catalog": False,
            "apikey": self.api_key,
            "seriesid": ["LNS14000000"],
            "startyear": year,
            "endyear": year,
        })
    
    def fetch_jolts(self, year: int, quarter: int) -> bytes:
        """Fetch JOLTS data for specific quarter."""
        return self.fetch("/observations/", {
            "validation": False,
            "catalog": False,
            "apikey": self.api_key,
            "seriesid": ["JTSJOLTS"],
            "startyear": year,
            "endyear": year,
            "calendar": "Q" + str(quarter),
        })
    
    def _build_url(self, series_id: str) -> str:
        """Build BLS API URL."""
        return f"{self.API_BASE}/observations/?seriesid={series_id}&apikey={self.api_key}"
```

---

## 8. Treasury Adapter Contract

**Version:** `adapter/treasury/v1`
**Module:** `macro_intelligence.adapters.treasury`
**Status:** Frozen

### 8.1 Treasury Adapter Overview

| Property | Value |
|----------|-------|
| Source Type | `treasury` |
| API Base URL | `https://api.fiscaldata.treasury.gov` |
| Rate Limit | Unlimited (no auth required) |
| Authentication | None required |
| Data Format | JSON |
| Supported Series | Treasury yield curves |

### 8.2 Treasury Adapter Interface

```python
class TreasuryAdapter(BaseAdapter):
    """
    Adapter for US Treasury data.
    
    Supported series:
    - US2Y, US5Y, US10Y, US30Y: Treasury constant maturities
    - Inverse yield curve spreads
    """
    
    SOURCE_TYPE = "treasury"
    API_BASE = "https://api.fiscaldata.treasury.gov/services/data/v1.1/treasury_amt"
    
    # Treasury constant maturity series
    SERIES_MAP = {
        "US2Y": "range_2_month",
        "US5Y": "range_5_year",
        "US10Y": "range_10_year",
        "US30Y": "range_30_year",
    }
    
    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "ResearchOS-Macro-Intelligence-Layer/1.0"
        })
    
    def adapt(self, raw_bytes: bytes, source_format: str = "json") -> list[RawRecord]:
        """
        Transform Treasury API response into RawRecord objects.
        """
        data = json.loads(raw_bytes.decode("utf-8"))
        records = []
        
        for record in data.get("data", []):
            records.append(RawRecord(
                source_id=self.SOURCE_TYPE,
                raw_key=record.get("range"),
                received_at=datetime.utcnow(),
                raw_payload={
                    "date": record.get("written_date"),
                    "value": record.get("value"),
                    "bc_period": record.get("bc_period"),
                },
                source_url=self.API_BASE,
            ))
        
        return records
    
    def parse_error(self, response: dict | bytes) -> AdapterError | None:
        """Parse Treasury API error response."""
        if isinstance(response, bytes):
            response = json.loads(response.decode("utf-8"))
        
        # Treasury API doesn't return structured errors
        return None
    
    def health_check(self) -> HealthResult:
        """Perform Treasury API health check."""
        start = datetime.utcnow()
        try:
            response = self._session.get(
                self.API_BASE,
                params={"filter": "range:eq:10-year"},
                timeout=10,
            )
            response_time = (datetime.utcnow() - start).total_seconds() * 1000
            
            if response.status_code == 200:
                return HealthResult(
                    status=HealthStatus.HEALTHY,
                    last_check=datetime.utcnow(),
                    last_success=datetime.utcnow(),
                    last_error=None,
                    response_time_ms=response_time,
                    consecutive_failures=0,
                )
            else:
                return HealthResult(
                    status=HealthStatus.DEGRADED,
                    last_check=datetime.utcnow(),
                    last_success=self._last_success,
                    last_error=f"HTTP {response.status_code}",
                    response_time_ms=response_time,
                    consecutive_failures=self._consecutive_failures,
                )
        except Exception as e:
            return HealthResult(
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow(),
                last_success=self._last_success,
                last_error=str(e),
                response_time_ms=(datetime.utcnow() - start).total_seconds() * 1000,
                consecutive_failures=self._consecutive_failures + 1,
            )
    
    def get_supported_series(self) -> list[str]:
        """Return list of Treasury-supported series IDs."""
        return list(self.SERIES_MAP.keys())
    
    def fetch_yield_curve(self, date: date) -> bytes:
        """Fetch yield curve data for specific date."""
        return self.fetch("", {
            "filter": f"written_date:gte:{date.isoformat()}",
        })
    
    def fetch_latest(self) -> bytes:
        """Fetch latest yield curve data."""
        return self.fetch("", {})
```

---

## 9. Federal Reserve Adapter Contract

**Version:** `adapter/fed/v1`
**Module:** `macro_intelligence.adapters.fed`
**Status:** Frozen

### 9.1 Federal Reserve Adapter Overview

| Property | Value |
|----------|-------|
| Source Type | `federal_reserve` |
| API Base URL | `https://www.federalreserve.gov` |
| Rate Limit | None (RSS feed) |
| Authentication | None required |
| Data Format | RSS/JSON |
| Supported Events | FOMC meetings, speeches, hearings |

### 9.2 Federal Reserve Adapter Interface

```python
class FederalReserveAdapter(BaseAdapter):
    """
    Adapter for Federal Reserve communications.
    
    Supported events:
    - FOMC meetings and statements
    - Fed Governor speeches
    - Congressional hearings
    """
    
    SOURCE_TYPE = "federal_reserve"
    FEED_URLS = {
        "fomc": "https://www.federalreserve.gov/feeds/fomcpress.xml",
        "speeches": "https://www.federalreserve.gov/feeds/board speeches.xml",
        "hearings": "https://www.federalreserve.gov/feeds/hearings.xml",
    }
    
    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "ResearchOS-Macro-Intelligence-Layer/1.0"
        })
    
    def adapt(self, raw_bytes: bytes, source_format: str = "xml") -> list[RawRecord]:
        """
        Transform RSS/Feed response into RawRecord objects.
        """
        import feedparser
        feed = feedparser.parse(raw_bytes)
        records = []
        
        for entry in feed.entries:
            records.append(RawRecord(
                source_id=self.SOURCE_TYPE,
                raw_key=entry.get("id", "unknown"),
                received_at=datetime.utcnow(),
                raw_payload={
                    "title": entry.get("title"),
                    "summary": entry.get("summary"),
                    "published": entry.get("published"),
                    "links": [link.get("href") for link in entry.get("links", [])],
                    "tags": [tag.get("term") for tag in entry.get("tags", [])],
                },
                source_url=entry.get("link"),
                format=source_format,
            ))
        
        return records
    
    def parse_error(self, response: dict | bytes) -> AdapterError | None:
        """Parse Federal Reserve feed error."""
        return None  # RSS feeds don't return structured errors
    
    def health_check(self) -> HealthResult:
        """Perform Federal Reserve feed health check."""
        start = datetime.utcnow()
        try:
            response = self._session.get(
                self.FEED_URLS["fomc"],
                timeout=10,
            )
            response_time = (datetime.utcnow() - start).total_seconds() * 1000
            
            if response.status_code == 200:
                import feedparser
                feed = feedparser.parse(response.content)
                if feed.entries:
                    return HealthResult(
                        status=HealthStatus.HEALTHY,
                        last_check=datetime.utcnow(),
                        last_success=datetime.utcnow(),
                        last_error=None,
                        response_time_ms=response_time,
                        consecutive_failures=0,
                    )
            
            return HealthResult(
                status=HealthStatus.DEGRADED,
                last_check=datetime.utcnow(),
                last_success=self._last_success,
                last_error="No entries in feed",
                response_time_ms=response_time,
                consecutive_failures=self._consecutive_failures,
            )
        except Exception as e:
            return HealthResult(
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow(),
                last_success=self._last_success,
                last_error=str(e),
                response_time_ms=(datetime.utcnow() - start).total_seconds() * 1000,
                consecutive_failures=self._consecutive_failures + 1,
            )
    
    def get_supported_series(self) -> list[str]:
        """Return list of supported event types."""
        return ["FOMC_MEETING", "FED_SPEECH", "FED_HEARING"]
    
    def fetch_fomc_feed(self) -> bytes:
        """Fetch FOMC feed."""
        return self.fetch("", {}, self.FEED_URLS["fomc"])
    
    def fetch_speeches_feed(self) -> bytes:
        """Fetch speeches feed."""
        return self.fetch("", {}, self.FEED_URLS["speeches"])
    
    def fetch_hearings_feed(self) -> bytes:
        """Fetch hearings feed."""
        return self.fetch("", {}, self.FEED_URLS["hearings"])
```

---

## 10. CFTC Adapter Contract

**Version:** `adapter/cftc/v1`
**Module:** `macro_intelligence.adapters.cftc`
**Status:** Frozen

### 10.1 CFTC Adapter Overview

| Property | Value |
|----------|-------|
| Source Type | `cftc` |
| API Base URL | `https://www.cftc.gov` |
| Rate Limit | 100 requests/minute |
| Authentication | None required |
| Data Format | CSV/XML |
| Supported Data | Commitments of Traders |

### 10.2 CFTC Adapter Interface

```python
class CFTCAdapter(BaseAdapter):
    """
    Adapter for CFTC Commitments of Traders data.
    
    Supports:
    - Disaggregated trades
    - Financial futures
    - Commercial positioning
    """
    
    SOURCE_TYPE = "cftc"
    API_BASE = "https://www.cftc.gov/dea/newcot"
    
    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "ResearchOS-Macro-Intelligence-Layer/1.0"
        })
    
    def adapt(self, raw_bytes: bytes, source_format: str = "csv") -> list[RawRecord]:
        """
        Transform CFTC CSV response into RawRecord objects.
        """
        import csv
        from io import StringIO
        
        text = raw_bytes.decode("utf-8")
        reader = csv.DictReader(StringIO(text))
        records = []
        
        for row in reader:
            # Parse CFTC-specific fields
            records.append(RawRecord(
                source_id=self.SOURCE_TYPE,
                raw_key=row.get("MarketCode", "UNKNOWN"),
                received_at=datetime.utcnow(),
                raw_payload={
                    "reportDate": row.get("Report Date"),
                    "marketCode": row.get("Market Code"),
                    "contractMultiplier": row.get("Contract Multiplier"),
                    "longCommercial": row.get("Long Commercial"),
                    "shortCommercial": row.get("Short Commercial"),
                    "longNonCommercial": row.get("Long Noncommercial"),
                    "shortNonCommercial": row.get("Short Noncommercial"),
                    "longNonreportable": row.get("Long Nonreportable"),
                    "shortNonreportable": row.get("Short Nonreportable"),
                },
                source_url=self.API_BASE,
                format=source_format,
            ))
        
        return records
    
    def parse_error(self, response: dict | bytes) -> AdapterError | None:
        """Parse CFTC API error."""
        return None
    
    def health_check(self) -> HealthResult:
        """Perform CFTC API health check."""
        start = datetime.utcnow()
        try:
            response = self._session.get(
                f"{self.API_BASE}/cftcotdataset.csv",
                timeout=10,
            )
            response_time = (datetime.utcnow() - start).total_seconds() * 1000
            
            if response.status_code == 200:
                return HealthResult(
                    status=HealthStatus.HEALTHY,
                    last_check=datetime.utcnow(),
                    last_success=datetime.utcnow(),
                    last_error=None,
                    response_time_ms=response_time,
                    consecutive_failures=0,
                )
            else:
                return HealthResult(
                    status=HealthStatus.DEGRADED,
                    last_check=datetime.utcnow(),
                    last_success=self._last_success,
                    last_error=f"HTTP {response.status_code}",
                    response_time_ms=response_time,
                    consecutive_failures=self._consecutive_failures,
                )
        except Exception as e:
            return HealthResult(
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow(),
                last_success=self._last_success,
                last_error=str(e),
                response_time_ms=(datetime.utcnow() - start).total_seconds() * 1000,
                consecutive_failures=self._consecutive_failures + 1,
            )
    
    def get_supported_series(self) -> list[str]:
        """Return list of supported CFTC markets."""
        return [
            "CL (Crude Oil)",
            "GC (Gold)",
            "SI (Silver)",
            "ES (E-mini S&P)",
            "NQ (E-mini Nasdaq)",
            "ZN (10-Year T-Note)",
            "ZB (30-Year T-Bond)",
        ]
    
    def fetch_latest(self) -> bytes:
        """Fetch latest COT data."""
        return self.fetch("/cftcotdataset.csv")
    
    def fetch_by_market(self, market_code: str) -> bytes:
        """Fetch COT data for specific market."""
        return self.fetch(f"/cftcotdataset_{market_code}.csv")
```

---

## 11. CBOE Adapter Contract

**Version:** `adapter/cboe/v1`
**Module:** `macro_intelligence.adapters.cboe`
**Status:** Frozen

### 11.1 CBOE Adapter Overview

| Property | Value |
|----------|-------|
| Source Type | `cboe` |
| API Base URL | `https://cdn.cboe.com/api` |
| Rate Limit | 30 requests/minute (free tier) |
| Authentication | API key required for some endpoints |
| Data Format | JSON/CSV |
| Supported Data | VIX, VXO, volatility indices |

### 11.2 CBOE Adapter Interface

```python
class CBOEAdapter(BaseAdapter):
    """
    Adapter for CBOE volatility data.
    
    Supported series:
    - VIX: CBOE Volatility Index
    - VXO: CBOE VIX on SPX
    - VX futures
    """
    
    SOURCE_TYPE = "cboe"
    API_BASE = "https://cdn.cboe.com/api"
    
    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self.api_key = config.credentials.get("api_key", "")
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "ResearchOS-Macro-Intelligence-Layer/1.0"
        })
    
    def adapt(self, raw_bytes: bytes, source_format: str = "json") -> list[RawRecord]:
        """
        Transform CBOE API response into RawRecord objects.
        """
        data = json.loads(raw_bytes.decode("utf-8"))
        records = []
        
        # Handle different CBOE response formats
        if isinstance(data, list):
            for item in data:
                records.append(RawRecord(
                    source_id=self.SOURCE_TYPE,
                    raw_key=item.get("symbol", "UNKNOWN"),
                    received_at=datetime.utcnow(),
                    raw_payload={
                        "timestamp": item.get("timestamp"),
                        "open": item.get("open"),
                        "high": item.get("high"),
                        "low": item.get("low"),
                        "close": item.get("close"),
                        "volume": item.get("volume"),
                    },
                    source_url=self.API_BASE,
                ))
        elif isinstance(data, dict):
            # Single value response
            records.append(RawRecord(
                source_id=self.SOURCE_TYPE,
                raw_key=data.get("symbol", "UNKNOWN"),
                received_at=datetime.utcnow(),
                raw_payload={
                    "value": data.get("value"),
                    "timestamp": data.get("timestamp"),
                },
                source_url=self.API_BASE,
            ))
        
        return records
    
    def parse_error(self, response: dict | bytes) -> AdapterError | None:
        """Parse CBOE API error response."""
        if isinstance(response, bytes):
            response = json.loads(response.decode("utf-8"))
        
        error_code = response.get("errorCode")
        error_message = response.get("errorMessage")
        
        if error_code:
            if error_code == 401:
                return AdapterError(
                    error_type=ErrorType.AUTH_ERROR,
                    message=error_message,
                    source_status_code=401,
                )
            elif error_code == 429:
                return AdapterError(
                    error_type=ErrorType.RATE_LIMIT,
                    message=error_message,
                    source_status_code=429,
                    retry_after=timedelta(seconds=2),
                )
            else:
                return AdapterError(
                    error_type=ErrorType.CLIENT_ERROR,
                    message=error_message,
                    source_status_code=error_code,
                )
        
        return None
    
    def health_check(self) -> HealthResult:
        """Perform CBOE API health check."""
        start = datetime.utcnow()
        try:
            response = self._session.get(
                f"{self.API_BASE}/options/vix/current",
                timeout=10,
            )
            response_time = (datetime.utcnow() - start).total_seconds() * 1000
            
            if response.status_code == 200:
                return HealthResult(
                    status=HealthStatus.HEALTHY,
                    last_check=datetime.utcnow(),
                    last_success=datetime.utcnow(),
                    last_error=None,
                    response_time_ms=response_time,
                    consecutive_failures=0,
                )
            else:
                return HealthResult(
                    status=HealthStatus.DEGRADED,
                    last_check=datetime.utcnow(),
                    last_success=self._last_success,
                    last_error=f"HTTP {response.status_code}",
                    response_time_ms=response_time,
                    consecutive_failures=self._consecutive_failures,
                )
        except Exception as e:
            return HealthResult(
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.utcnow(),
                last_success=self._last_success,
                last_error=str(e),
                response_time_ms=(datetime.utcnow() - start).total_seconds() * 1000,
                consecutive_failures=self._consecutive_failures + 1,
            )
    
    def get_supported_series(self) -> list[str]:
        """Return list of CBOE-supported series."""
        return ["VIX", "VXO", "VIX_FUTURES"]
    
    def fetch_vix(self) -> bytes:
        """Fetch current VIX."""
        return self.fetch("/options/vix/current")
    
    def fetch_vix_history(self, days: int = 30) -> bytes:
        """Fetch VIX historical data."""
        return self.fetch(f"/options/vix/history?length={days}")
    
    def fetch_vxo(self) -> bytes:
        """Fetch current VXO."""
        return self.fetch("/options/vxo/current")
```

---

## 12. Adapter Lifecycle

### 12.1 Lifecycle States

```
                    ┌─────────────┐
                    │   CREATED   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
              ┌─────│   INIT      │─────┐
              │     └──────┬──────┘     │
              │            │            │
              │            ▼            │
              │     ┌─────────────┐     │
              │     │   HEALTHY   │     │
              │     └──────┬──────┘     │
              │            │            │
              │     ┌──────┴──────┐     │
              │     │  INGING DATA │     │
              │     └──────┬──────┘     │
              │            │            │
              │            ▼            │
              │     ┌─────────────┐     │
              │     │  DEGRADED   │◄────┘
              │     └──────┬──────┘
              │            │
              │            ▼
              │     ┌─────────────┐
              │     │  UNHEALTHY  │
              │     └──────┬──────┘
              │            │
              └────────────┼────────────
                           │
                           ▼
                    ┌─────────────┐
                    │   SHUTDOWN  │
                    └─────────────┘
```

### 12.2 Lifecycle Methods

```python
class BaseAdapter(ABC):
    """
    Abstract base class for all macro data source adapters.
    """
    
    def init(self) -> None:
        """Initialize adapter (called once at startup)."""
        logger.info(f"Initializing {self.SOURCE_TYPE} adapter")
        self._validate_credentials()
        self._connect()
    
    def shutdown(self) -> None:
        """Shutdown adapter (called at exit)."""
        logger.info(f"Shutting down {self.SOURCE_TYPE} adapter")
        self._session.close()
        self.cache.clear()
    
    def _validate_credentials(self) -> None:
        """Validate adapter credentials."""
        if hasattr(self, 'api_key') and not self.api_key:
            logger.warning(f"{self.SOURCE_TYPE} adapter: No API key configured")
    
    def _connect(self) -> None:
        """Test connection to source."""
        result = self.health_check()
        if result.status != HealthStatus.HEALTHY:
            logger.warning(f"{self.SOURCE_TYPE} adapter: Initial health check failed")
```

---

## 13. Health Monitoring

### 13.1 Health Check Schedule

| Source | Check Frequency | Timeout |
|--------|----------------|---------|
| FRED | Every 5 minutes | 10 seconds |
| BLS | Every 5 minutes | 10 seconds |
| Treasury | Every 1 minute | 5 seconds |
| Federal Reserve | Every 15 minutes | 10 seconds |
| CFTC | Every 10 minutes | 10 seconds |
| CBOE | Every 1 minute | 5 seconds |

### 13.2 Health Alert Thresholds

| Metric | Warning Threshold | Critical Threshold |
|--------|------------------|-------------------|
| Consecutive failures | 3 | 5 |
| Response time | 5 seconds | 10 seconds |
| Failure rate (1h) | 10% | 50% |
| Rate limit hits | 5 | 10 |

---

## 14. Testing Strategy

### 14.1 Test Categories

| Test Type | Description | Coverage Target |
|-----------|-------------|-----------------|
| Unit Tests | Individual adapter methods | 90% |
| Integration Tests | Live API calls (mocked) | 80% |
| Contract Tests | Adapter interface compliance | 100% |
| Performance Tests | Latency and throughput | Critical paths |
| Failure Tests | Error handling and recovery | 100% |

### 14.2 Test Fixtures

```python
# tests/fixtures/adapters/
├── fred_responses/
│   ├── gdp_observations.json
│   ├── cpi_observations.json
│   └── error_responses.json
├── bls_responses/
│   ├── cpi_observations.json
│   ├── unemployment_observations.json
│   └── error_responses.json
├── treasury_responses/
│   ├── yield_curve.json
│   └── latest_quotes.json
├── cboe_responses/
│   ├── vix_current.json
│   └── vix_history.json
└── fed_responses/
    ├── fomc_feed.xml
    └── speeches_feed.xml
```

---

## Final Declaration

---

**Macro Intelligence Layer Source Adapter Architecture is architecturally frozen and ready for implementation.**

All adapter contracts are versioned, isolated, and fault-tolerant. The architecture supports:
- 6 production adapters (FRED, BLS, Treasury, Federal Reserve, CFTC, CBOE)
- Centralized retry and rate limiting
- Circuit breaker failure isolation
- Comprehensive health monitoring
- Deterministic caching

**Next Step:** Begin implementation of adapter registry and base adapter framework.

---

*Document Version: 1.0.0-frozen*
*Last Updated: 2026-08-03*
*Classification: Internal — Quantitative Platform Architecture*
