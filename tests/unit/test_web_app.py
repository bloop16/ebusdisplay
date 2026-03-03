"""
Test suite for Flask web interface.
TDD: Tests FIRST!
"""
import pytest
import json


@pytest.fixture
def client():
    """Flask test client"""
    from src.web.app import create_app
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client


class TestWebInterface:
    """Test Flask web interface"""
    
    def test_index_page_loads(self, client):
        """Homepage should load"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Bus Display' in response.data or b'bus' in response.data.lower()
    
    def test_api_search_stops(self, client):
        """API endpoint for stop search"""
        response = client.get('/api/stops?q=Bregenz')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        if len(data) > 0:
            assert 'id' in data[0]
            assert 'name' in data[0]
    
    def test_api_get_departures(self, client):
        """API endpoint for departures"""
        response = client.get('/api/departures?stop_id=test_stop')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        if len(data) > 0:
            assert 'line' in data[0]
            assert 'destination' in data[0]
            assert 'departure_time' in data[0]
    
    def test_api_save_config(self, client):
        """Should save bus stop configuration"""
        config = {
            'stops': [
                {'id': '1', 'name': 'Bregenz Bahnhof'},
                {'id': '2', 'name': 'Bregenz Hafen'}
            ]
        }
        
        response = client.post(
            '/api/config',
            data=json.dumps(config),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
    
    def test_api_get_config(self, client):
        """Should retrieve current configuration"""
        response = client.get('/api/config')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'stops' in data
        assert isinstance(data['stops'], list)
    
    def test_api_missing_param_returns_400(self, client):
        """API should return 400 for missing parameters"""
        response = client.get('/api/departures')  # Missing stop_id
        assert response.status_code == 400
