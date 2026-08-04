"""
ResearchOS Macro Intelligence Layer - Time & Calendar Tests
"""

import pytest
from datetime import datetime, timezone, timedelta

UTC = timezone.utc


class TestTimeNormalizer:
    """Tests for TimeNormalizer."""
    
    def test_to_utc_preserves_utc(self):
        """Test that UTC datetimes remain unchanged."""
        from macro_intelligence.time.normalizer import TimeNormalizer
        
        dt = datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
        result = TimeNormalizer.to_utc(dt)
        
        assert result == dt
        assert result.tzinfo == UTC
    
    def test_to_utc_converts_timezone(self):
        """Test timezone conversion to UTC."""
        from macro_intelligence.time.normalizer import TimeNormalizer
        
        # Create datetime in US Eastern (UTC-5)
        eastern = timezone(timedelta(hours=-5))
        dt = datetime(2026, 8, 3, 12, 0, 0, tzinfo=eastern)
        
        result = TimeNormalizer.to_utc(dt)
        
        # 12:00 ET = 17:00 UTC
        assert result.hour == 17
        assert result.tzinfo == UTC
    
    def test_to_utc_handles_naive(self):
        """Test naive datetime handling."""
        from macro_intelligence.time.normalizer import TimeNormalizer
        
        dt = datetime(2026, 8, 3, 12, 0, 0)
        result = TimeNormalizer.to_utc(dt)
        
        # Naive datetime should be assumed UTC
        assert result.tzinfo == UTC
    
    def test_normalize_timestamp(self):
        """Test timestamp normalization."""
        from macro_intelligence.time.normalizer import TimeNormalizer
        
        dt = datetime(2026, 8, 3, 12, 30, 45, 123456, tzinfo=UTC)
        result = TimeNormalizer.normalize_timestamp(dt)
        
        # Should round down to second
        assert result.microsecond == 0
        assert result.second == 45
    
    def test_normalize_to_minute(self):
        """Test minute normalization."""
        from macro_intelligence.time.normalizer import TimeNormalizer
        
        dt = datetime(2026, 8, 3, 12, 30, 45, 123456, tzinfo=UTC)
        result = TimeNormalizer.normalize_to_minute(dt)
        
        # Should round down to minute
        assert result.second == 0
        assert result.microsecond == 0
        assert result.minute == 30
    
    def test_normalize_to_hour(self):
        """Test hour normalization."""
        from macro_intelligence.time.normalizer import TimeNormalizer
        
        dt = datetime(2026, 8, 3, 12, 30, 45, 123456, tzinfo=UTC)
        result = TimeNormalizer.normalize_to_hour(dt)
        
        # Should round down to hour
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0
        assert result.hour == 12
    
    def test_normalize_to_day(self):
        """Test day normalization."""
        from macro_intelligence.time.normalizer import TimeNormalizer
        
        dt = datetime(2026, 8, 3, 12, 30, 45, 123456, tzinfo=UTC)
        result = TimeNormalizer.normalize_to_day(dt)
        
        # Should round down to start of day
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0
    
    def test_get_deterministic_timestamp(self):
        """Test deterministic timestamp generation."""
        from macro_intelligence.time.normalizer import TimeNormalizer
        
        dt = datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
        result = TimeNormalizer.get_deterministic_timestamp(dt)
        
        assert result == "2026-08-03T12:00:00+00:00"
    
    def test_parse_deterministic_timestamp(self):
        """Test deterministic timestamp parsing."""
        from macro_intelligence.time.normalizer import TimeNormalizer
        
        ts = "2026-08-03T12:00:00+00:00"
        result = TimeNormalizer.parse_deterministic_timestamp(ts)
        
        assert result.year == 2026
        assert result.month == 8
        assert result.day == 3
        assert result.hour == 12
        assert result.tzinfo == UTC
    
    def test_deterministic_roundtrip(self):
        """Test deterministic roundtrip."""
        from macro_intelligence.time.normalizer import TimeNormalizer
        
        dt = datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
        ts = TimeNormalizer.get_deterministic_timestamp(dt)
        restored = TimeNormalizer.parse_deterministic_timestamp(ts)
        
        assert restored == dt


class TestPlannedRelease:
    """Tests for PlannedRelease."""
    
    def test_create_release(self):
        """Test creating a planned release."""
        from macro_intelligence.time.schedule import PlannedRelease
        from macro_intelligence.time.enums import ReleaseStatus
        
        release = PlannedRelease(
            release_id="REL_20260803_001",
            event_id="EVT_20260803_001",
            series_id="SER_20260803_001",
            planned_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            status=ReleaseStatus.PLANNED,
        )
        
        assert release.release_id == "REL_20260803_001"
        assert release.status == ReleaseStatus.PLANNED
    
    def test_release_immutability(self):
        """Test that release is immutable."""
        from macro_intelligence.time.schedule import PlannedRelease
        from macro_intelligence.time.enums import ReleaseStatus
        
        release = PlannedRelease(
            release_id="REL_20260803_001",
            event_id="EVT_20260803_001",
            series_id="SER_20260803_001",
            planned_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            status=ReleaseStatus.PLANNED,
        )
        
        with pytest.raises(AttributeError):
            release.status = ReleaseStatus.COMPLETED
    
    def test_release_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        from macro_intelligence.time.schedule import PlannedRelease
        from macro_intelligence.time.enums import ReleaseStatus
        
        original = PlannedRelease(
            release_id="REL_20260803_001",
            event_id="EVT_20260803_001",
            series_id="SER_20260803_001",
            planned_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            status=ReleaseStatus.PLANNED,
        )
        
        json_str = original.to_json()
        restored = PlannedRelease.from_json(json_str)
        
        assert restored.release_id == original.release_id
        assert restored.to_json() == json_str
    
    def test_release_hash_deterministic(self):
        """Test that hash is deterministic."""
        from macro_intelligence.time.schedule import PlannedRelease
        from macro_intelligence.time.enums import ReleaseStatus
        
        release1 = PlannedRelease(
            release_id="REL_20260803_001",
            event_id="EVT_20260803_001",
            series_id="SER_20260803_001",
            planned_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            status=ReleaseStatus.PLANNED,
        )
        
        release2 = PlannedRelease(
            release_id="REL_20260803_001",
            event_id="EVT_20260803_001",
            series_id="SER_20260803_001",
            planned_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            status=ReleaseStatus.PLANNED,
        )
        
        assert release1.compute_hash() == release2.compute_hash()
    
    def test_release_validate(self):
        """Test release validation."""
        from macro_intelligence.time.schedule import PlannedRelease
        from macro_intelligence.time.enums import ReleaseStatus
        
        release = PlannedRelease(
            release_id="REL_20260803_001",
            event_id="EVT_20260803_001",
            series_id="SER_20260803_001",
            planned_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            status=ReleaseStatus.PLANNED,
        )
        
        is_valid, errors = release.validate()
        assert is_valid
        assert len(errors) == 0
    
    def test_release_validate_invalid_id(self):
        """Test release validation with invalid ID."""
        from macro_intelligence.time.schedule import PlannedRelease
        from macro_intelligence.time.enums import ReleaseStatus
        
        release = PlannedRelease(
            release_id="INVALID",
            event_id="EVT_20260803_001",
            series_id="SER_20260803_001",
            planned_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            status=ReleaseStatus.PLANNED,
        )
        
        is_valid, errors = release.validate()
        assert not is_valid
        assert any("release_id" in e for e in errors)


class TestCalendarEvent:
    """Tests for CalendarEvent."""
    
    def test_create_event(self):
        """Test creating a calendar event."""
        from macro_intelligence.time.timeline import CalendarEvent
        from macro_intelligence.time.enums import EventCategory
        
        event = CalendarEvent(
            event_id="EVT_20260803_001",
            event_type=EventCategory.DATA_RELEASE,
            scheduled_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            title="CPI Release",
        )
        
        assert event.event_id == "EVT_20260803_001"
        assert event.event_type == EventCategory.DATA_RELEASE
    
    def test_event_immutability(self):
        """Test that event is immutable."""
        from macro_intelligence.time.timeline import CalendarEvent
        from macro_intelligence.time.enums import EventCategory
        
        event = CalendarEvent(
            event_id="EVT_20260803_001",
            event_type=EventCategory.DATA_RELEASE,
            scheduled_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            title="CPI Release",
        )
        
        with pytest.raises(AttributeError):
            event.title = "Modified"
    
    def test_event_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        from macro_intelligence.time.timeline import CalendarEvent
        from macro_intelligence.time.enums import EventCategory
        
        original = CalendarEvent(
            event_id="EVT_20260803_001",
            event_type=EventCategory.DATA_RELEASE,
            scheduled_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            title="CPI Release",
        )
        
        json_str = original.to_json()
        restored = CalendarEvent.from_json(json_str)
        
        assert restored.event_id == original.event_id
        assert restored.to_json() == json_str
    
    def test_event_hash_deterministic(self):
        """Test that hash is deterministic."""
        from macro_intelligence.time.timeline import CalendarEvent
        from macro_intelligence.time.enums import EventCategory
        
        event1 = CalendarEvent(
            event_id="EVT_20260803_001",
            event_type=EventCategory.DATA_RELEASE,
            scheduled_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            title="CPI Release",
        )
        
        event2 = CalendarEvent(
            event_id="EVT_20260803_001",
            event_type=EventCategory.DATA_RELEASE,
            scheduled_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            title="CPI Release",
        )
        
        assert event1.compute_hash() == event2.compute_hash()


class TestTimeWindow:
    """Tests for TimeWindow."""
    
    def test_window_contains(self):
        """Test window containment."""
        from macro_intelligence.time.timeline import TimeWindow
        from macro_intelligence.time.enums import WindowType
        
        event_time = datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
        window = TimeWindow(
            window_type=WindowType.PRE_EVENT,
            start=event_time - timedelta(hours=1),
            end=event_time,
            event_time=event_time,
        )
        
        # Time within window
        assert window.contains(event_time - timedelta(minutes=30))
        
        # Time before window
        assert not window.contains(event_time - timedelta(hours=2))
        
        # Time after window
        assert not window.contains(event_time + timedelta(minutes=30))
    
    def test_window_duration(self):
        """Test window duration calculation."""
        from macro_intelligence.time.timeline import TimeWindow
        from macro_intelligence.time.enums import WindowType
        
        event_time = datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
        window = TimeWindow(
            window_type=WindowType.POST_EVENT,
            start=event_time,
            end=event_time + timedelta(hours=1),
            event_time=event_time,
        )
        
        assert window.duration() == timedelta(hours=1)


class TestEconomicCalendar:
    """Tests for EconomicCalendar."""
    
    def test_create_calendar(self):
        """Test creating an economic calendar."""
        from macro_intelligence.time.calendar import EconomicCalendar
        
        calendar = EconomicCalendar(
            calendar_id="CAL_2026_08",
            year=2026,
            month=8,
        )
        
        assert calendar.calendar_id == "CAL_2026_08"
        assert calendar.year == 2026
        assert calendar.month == 8
    
    def test_add_event(self):
        """Test adding an event to calendar."""
        from macro_intelligence.time.calendar import EconomicCalendar
        from macro_intelligence.time.timeline import CalendarEvent
        from macro_intelligence.time.enums import EventCategory
        
        calendar = EconomicCalendar(
            calendar_id="CAL_2026_08",
            year=2026,
            month=8,
        )
        
        event = CalendarEvent(
            event_id="EVT_001",
            event_type=EventCategory.DATA_RELEASE,
            scheduled_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            title="CPI Release",
        )
        
        new_calendar = calendar.add_event(event)
        
        assert new_calendar.get_event_count() == 1
        assert calendar.get_event_count() == 0  # Original unchanged
    
    def test_is_trading_day(self):
        """Test trading day detection."""
        from macro_intelligence.time.calendar import EconomicCalendar
        
        calendar = EconomicCalendar(
            calendar_id="CAL_2026_08",
            year=2026,
            month=8,
        )
        
        # Tuesday is a trading day
        tuesday = datetime(2026, 8, 4, 12, 0, 0, tzinfo=UTC)
        assert calendar.is_trading_day(tuesday) is True
        
        # Saturday is not a trading day
        saturday = datetime(2026, 8, 8, 12, 0, 0, tzinfo=UTC)
        assert calendar.is_trading_day(saturday) is False
        
        # Sunday is not a trading day
        sunday = datetime(2026, 8, 9, 12, 0, 0, tzinfo=UTC)
        assert calendar.is_trading_day(sunday) is False
    
    def test_is_holiday(self):
        """Test holiday detection."""
        from macro_intelligence.time.calendar import EconomicCalendar, MarketHoliday
        
        calendar = EconomicCalendar(
            calendar_id="CAL_2026_08",
            year=2026,
            month=8,
        )
        
        # Add a holiday
        holiday = MarketHoliday(
            holiday_id="HOL_001",
            date=datetime(2026, 8, 3, tzinfo=UTC),
            name="Test Holiday",
        )
        
        new_calendar = calendar.add_holiday(holiday)
        
        assert new_calendar.is_holiday(holiday.date) is True
        assert calendar.is_holiday(holiday.date) is False  # Original unchanged
    
    def test_get_next_trading_day(self):
        """Test next trading day calculation."""
        from macro_intelligence.time.calendar import EconomicCalendar
        
        calendar = EconomicCalendar(
            calendar_id="CAL_2026_08",
            year=2026,
            month=8,
        )
        
        # Friday
        friday = datetime(2026, 8, 7, 12, 0, 0, tzinfo=UTC)
        next_day = calendar.get_next_trading_day(friday)
        
        # Should skip weekend
        assert next_day.weekday() == 0  # Monday
    
    def test_get_previous_trading_day(self):
        """Test previous trading day calculation."""
        from macro_intelligence.time.calendar import EconomicCalendar
        
        calendar = EconomicCalendar(
            calendar_id="CAL_2026_08",
            year=2026,
            month=8,
        )
        
        # Monday
        monday = datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
        prev_day = calendar.get_previous_trading_day(monday)
        
        # Should go back to Friday
        assert prev_day.weekday() == 4  # Friday
    
    def test_calendar_integrity(self):
        """Test calendar integrity verification."""
        from macro_intelligence.time.calendar import EconomicCalendar
        
        calendar = EconomicCalendar(
            calendar_id="CAL_2026_08",
            year=2026,
            month=8,
        )
        
        is_valid, errors = calendar.verify_integrity()
        assert is_valid
        assert len(errors) == 0


class TestMILTimeInvariants:
    """Tests for MIL-TIME invariants."""
    
    def test_mil_time_001_utc_storage(self):
        """MIL-TIME-001: All timestamps are stored in UTC."""
        from macro_intelligence.time.normalizer import TimeNormalizer
        from macro_intelligence.time.schedule import PlannedRelease
        from macro_intelligence.time.enums import ReleaseStatus
        
        release = PlannedRelease(
            release_id="REL_001",
            event_id="EVT_001",
            series_id="SER_001",
            planned_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            status=ReleaseStatus.PLANNED,
        )
        
        is_valid, errors = release.validate()
        assert is_valid
        assert not any("UTC" in e for e in errors)
    
    def test_mil_time_002_immutable_history(self):
        """MIL-TIME-002: Release history is immutable."""
        from macro_intelligence.time.schedule import PlannedRelease, ReleaseSchedule
        from macro_intelligence.time.enums import ReleaseStatus
        
        release = PlannedRelease(
            release_id="REL_001",
            event_id="EVT_001",
            series_id="SER_001",
            planned_time=datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC),
            status=ReleaseStatus.PLANNED,
        )
        
        schedule = ReleaseSchedule(
            series_id="SER_001",
            releases=[release],
        )
        
        # Should not be able to modify existing release
        with pytest.raises(AttributeError):
            schedule.releases[0].status = ReleaseStatus.COMPLETED
    
    def test_mil_time_003_deterministic_windows(self):
        """MIL-TIME-003: Market reaction windows are deterministic."""
        from macro_intelligence.time.timeline import EventWindowSpec
        
        spec = EventWindowSpec()
        event_time = datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
        
        windows = spec.generate_windows(event_time)
        
        # Generate again
        windows2 = spec.generate_windows(event_time)
        
        # Should be identical
        assert len(windows) == len(windows2)
        for w1, w2 in zip(windows, windows2):
            assert w1.start == w2.start
            assert w1.end == w2.end
    
    def test_mil_time_004_reproducible_calendar(self):
        """MIL-TIME-004: Calendar reconstruction is reproducible."""
        from macro_intelligence.time.calendar import EconomicCalendar
        
        calendar1 = EconomicCalendar(
            calendar_id="CAL_2026_08",
            year=2026,
            month=8,
        )
        
        calendar2 = EconomicCalendar(
            calendar_id="CAL_2026_08",
            year=2026,
            month=8,
        )
        
        # Should be identical
        assert calendar1.to_dict() == calendar2.to_dict()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
