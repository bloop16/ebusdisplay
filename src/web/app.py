"""
Flask web interface for bus display configuration.
"""
from flask import Flask, render_template, jsonify, request
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def create_app(testing=False):
    """Application factory"""
    app = Flask(__name__)
    app.config['TESTING'] = testing
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    CONFIG_DIR = BASE_DIR / 'config'
    CONFIG_FILE = CONFIG_DIR / 'stops.json'
    
    # Ensure config dir exists
    CONFIG_DIR.mkdir(exist_ok=True)
    
    # Import API client
    from src.api import VMobilAPI
    api = VMobilAPI()
    
    @app.route('/')
    def index():
        """Homepage"""
        return render_template('index.html')
    
    @app.route('/api/stops')
    def api_search_stops():
        """Search bus stops"""
        query = request.args.get('q', '')
        
        if not query:
            return jsonify([])
        
        try:
            stops = api.search_stops(query)
            return jsonify(stops)
        except Exception as e:
            logger.error(f'Stop search failed: {e}')
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/departures')
    def api_get_departures():
        """Get departures for a stop"""
        stop_id = request.args.get('stop_id')
        
        if not stop_id:
            return jsonify({'error': 'stop_id required'}), 400
        
        try:
            limit = int(request.args.get('limit', 10))
            departures = api.get_departures(stop_id=stop_id, limit=limit)
            
            # Convert to dict for JSON
            return jsonify([dep.to_dict() for dep in departures])
        except Exception as e:
            logger.error(f'Departure fetch failed: {e}')
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/config', methods=['GET', 'POST'])
    def api_config():
        """Get or save configuration"""
        if request.method == 'GET':
            # Load config
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE) as f:
                    config = json.load(f)
            else:
                config = {'stops': []}
            
            return jsonify(config)
        
        else:  # POST
            # Save config
            try:
                config = request.get_json()
                
                if not config or 'stops' not in config:
                    return jsonify({'error': 'Invalid config'}), 400
                
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(config, f, indent=2)
                
                logger.info(f'Config saved: {len(config["stops"])} stops')
                return jsonify({'status': 'ok'})
            
            except Exception as e:
                logger.error(f'Config save failed: {e}')
                return jsonify({'error': str(e)}), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
