"""
ResearchOS Macro Intelligence Layer - Revision Enumerations
Version: rev/enums/v1
Status: FROZEN
"""

from enum import Enum


class RevisionState(str, Enum):
    """
    Revision state enumeration.

    States:
    - ORIGINAL: Initial creation of the object
    - REVISED: Updated with new information
    - CORRECTED: Error in previous version fixed
    - SUPERSEDED: Replaced by a newer version
    - DEPRECATED: No longer used, retained for history
    """

    ORIGINAL = "original"
    REVISED = "revised"
    CORRECTED = "corrected"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"

    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self in (
            RevisionState.SUPERSEDED,
            RevisionState.DEPRECATED,
        )

    def is_intermediate(self) -> bool:
        """Check if this is an intermediate state."""
        return self in (
            RevisionState.ORIGINAL,
            RevisionState.REVISED,
            RevisionState.CORRECTED,
        )

    def can_transition_to(self, target: "RevisionState") -> bool:
        """Check if transition to target state is allowed."""
        transitions = {
            RevisionState.ORIGINAL: {
                RevisionState.REVISED,
                RevisionState.CORRECTED,
                RevisionState.SUPERSEDED,
                RevisionState.DEPRECATED,
            },
            RevisionState.REVISED: {
                RevisionState.REVISED,
                RevisionState.CORRECTED,
                RevisionState.SUPERSEDED,
                RevisionState.DEPRECATED,
            },
            RevisionState.CORRECTED: {
                RevisionState.REVISED,
                RevisionState.CORRECTED,
                RevisionState.SUPERSEDED,
                RevisionState.DEPRECATED,
            },
            RevisionState.SUPERSEDED: set(),  # Terminal
            RevisionState.DEPRECATED: set(),  # Terminal
        }
        return target in transitions.get(self, set())


class RevisionType(str, Enum):
    """
    Type of revision operation.

    Types:
    - DATA_UPDATE: New data value received
    - DATA_CORRECTION: Error in previous data fixed
    - FORECAST_UPDATE: Consensus forecast updated
    - METHODOLOGY_CHANGE: Calculation method changed
    - SOURCE_CHANGE: Data source changed
    - CLASSIFICATION_UPDATE: Classification updated
    """

    DATA_UPDATE = "data_update"
    DATA_CORRECTION = "data_correction"
    FORECAST_UPDATE = "forecast_update"
    METHODOLOGY_CHANGE = "methodology_change"
    SOURCE_CHANGE = "source_change"
    CLASSIFICATION_UPDATE = "classification_update"

    def is_corrective(self) -> bool:
        """Check if this is a corrective revision."""
        return self in (
            RevisionType.DATA_CORRECTION,
            RevisionType.METHODOLOGY_CHANGE,
        )

    def is_additive(self) -> bool:
        """Check if this is an additive revision."""
        return self in (
            RevisionType.DATA_UPDATE,
            RevisionType.FORECAST_UPDATE,
        )


class ProvenanceSource(str, Enum):
    """
    Source type enumeration for provenance tracking.

    Types:
    - FRED: Federal Reserve Economic Data
    - BLS: Bureau of Labor Statistics
    - CBOE: Chicago Board Options Exchange
    - CFTC: Commodity Futures Trading Commission
    - ISM: Institute for Supply Management
    - TREASURY: US Treasury
    - FED: Federal Reserve
    - BEA: Bureau of Economic Analysis
    - OTHER: Other source
    """

    FRED = "fred"
    BLS = "bls"
    CBOE = "cboe"
    CFTC = "cftc"
    ISM = "ism"
    TREASURY = "treasury"
    FED = "fed"
    BEA = "bea"
    OTHER = "other"

    @classmethod
    def from_string(cls, source: str) -> "ProvenanceSource":
        """Convert string to enum value."""
        source_lower = source.lower()
        mapping = {
            "fred": cls.FRED,
            "bls": cls.BLS,
            "cboe": cls.CBOE,
            "cftc": cls.CFTC,
            "ism": cls.ISM,
            "treasury": cls.TREASURY,
            "fed": cls.FED,
            "bea": cls.BEA,
            "ice": cls.FRED,  # ICE for DXY
            "goldman": cls.CFTC,  # Goldman for MOVE
        }
        return mapping.get(source_lower, cls.OTHER)


class AuditAction(str, Enum):
    """
    Audit action enumeration.

    Actions:
    - CREATE: Object created
    - UPDATE: Object updated (new revision)
    - VALIDATE: Object validated
    - AUDIT: Object audited
    - RECONSTRUCT: Historical state reconstructed
    - VERIFY: Integrity verified
    """

    CREATE = "create"
    UPDATE = "update"
    VALIDATE = "validate"
    AUDIT = "audit"
    RECONSTRUCT = "reconstruct"
    VERIFY = "verify"

    def is_write_operation(self) -> bool:
        """Check if this is a write operation."""
        return self in (
            AuditAction.CREATE,
            AuditAction.UPDATE,
        )

    def is_read_operation(self) -> bool:
        """Check if this is a read operation."""
        return self in (
            AuditAction.VALIDATE,
            AuditAction.AUDIT,
            AuditAction.RECONSTRUCT,
            AuditAction.VERIFY,
        )


class IntegrityLevel(str, Enum):
    """
    Integrity verification level.

    Levels:
    - BASIC: Basic format checks
    - STANDARD: Standard validation
    - STRICT: Strict validation with cross-checks
    - FULL: Full integrity verification
    """

    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    FULL = "full"

    @classmethod
    def from_string(cls, level: str) -> "IntegrityLevel":
        """Convert string to enum value."""
        mapping = {
            "basic": cls.BASIC,
            "standard": cls.STANDARD,
            "strict": cls.STRICT,
            "full": cls.FULL,
        }
        return mapping.get(level.lower(), cls.STANDARD)
