"""
Test suite for vmobil.at bus departure fetching.
TDD: Write tests FIRST, then implement!
"""
import pytest
from datetime import datetime, timedelta


class TestVMobilAPI:
    """Test vmobil.at data fetching"""
    
    def test_search_stop_by_name(self):
        """Should find bus stops by name"""
        from src.api.vmobil import VMobilAPI
        
        api = VMobilAPI()
        stops = api.search_stops("Bregenz Bahnhof")
        
        assert len(stops) > 0
        assert any("Bregenz" in stop['name'] for stop in stops)
        assert all('id' in stop for stop in stops)
        assert all('name' in stop for stop in stops)
    
    def test_get_departures_for_stop(self):
        """Should fetch next departures for a bus stop"""
        from src.api.vmobil import VMobilAPI, Departure
        
        api = VMobilAPI()
        
        # Use a known stop ID (we'll determine this during implementation)
        departures = api.get_departures(stop_id="test_stop", limit=5)
        
        assert len(departures) <= 5
        assert all(isinstance(dep, Departure) for dep in departures)
        assert all(hasattr(dep, 'line') for dep in departures)
        assert all(hasattr(dep, 'destination') for dep in departures)
        assert all(hasattr(dep, 'departure_time') for dep in departures)
    
    def test_departure_time_parsing(self):
        """Should parse departure times correctly"""
        from src.api.vmobil import VMobilAPI
        
        api = VMobilAPI()
        
        # Test various time formats that vmobil.at might return
        test_cases = [
            ("14:35", datetime.now().replace(hour=14, minute=35, second=0, microsecond=0)),
            ("09:05", datetime.now().replace(hour=9, minute=5, second=0, microsecond=0)),
        ]
        
        for time_str, expected in test_cases:
            parsed = api._parse_time(time_str)
            assert parsed.hour == expected.hour
            assert parsed.minute == expected.minute
    
    def test_handle_delays(self):
        """Should handle delay information if available"""
        from src.api.vmobil import VMobilAPI
        
        api = VMobilAPI()
        departures = api.get_departures(stop_id="test_stop", limit=3)
        
        # Delays might be optional
        for dep in departures:
            if hasattr(dep, 'delay_minutes') and dep.delay_minutes is not None:
                assert isinstance(dep.delay_minutes, int)
                assert dep.delay_minutes >= 0
    
    def test_empty_stop_returns_empty_list(self):
        """Should return empty list for non-existent stops"""
        from src.api.vmobil import VMobilAPI
        
        api = VMobilAPI()
        stops = api.search_stops("NONEXISTENT_STOP_XYZ123")
        
        assert isinstance(stops, list)
        assert len(stops) == 0
    
    def test_invalid_stop_id_raises_error(self):
        """Should raise error for invalid stop ID"""
        from src.api.vmobil import VMobilAPI, VMobilAPIError
        
        api = VMobilAPI()
        
        with pytest.raises(VMobilAPIError):
            api.get_departures(stop_id=None)


class TestDepartureData:
    """Test departure data structure"""
    
    def test_departure_has_required_fields(self):
        """Departure object must have all required fields"""
        from src.api.vmobil import Departure
        
        dep = Departure(
            line="1",
            destination="Bregenz Bahnhof",
            departure_time=datetime.now() + timedelta(minutes=5),
            stop_name="Lochau Kirche"
        )
        
        assert dep.line == "1"
        assert dep.destination == "Bregenz Bahnhof"
        assert isinstance(dep.departure_time, datetime)
        assert dep.stop_name == "Lochau Kirche"
    
    def test_departure_delay_optional(self):
        """Delay information should be optional"""
        from src.api.vmobil import Departure
        
        dep = Departure(
            line="5",
            destination="Dornbirn",
            departure_time=datetime.now(),
            stop_name="Test Stop"
        )
        
        assert not hasattr(dep, 'delay_minutes') or dep.delay_minutes is None
    
    def test_departure_to_dict(self):
        """Should convert to dictionary for JSON serialization"""
        from src.api.vmobil import Departure
        
        now = datetime.now()
        dep = Departure(
            line="3",
            destination="Bludenz",
            departure_time=now,
            stop_name="Test"
        )
        
        data = dep.to_dict()
        
        assert data['line'] == "3"
        assert data['destination'] == "Bludenz"
        assert 'departure_time' in data
        assert data['stop_name'] == "Test"
