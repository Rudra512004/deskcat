from flask import Flask, request, jsonify
import threading
import logging

def start_server(event_queue):
    # Disable flask logging to keep console clean
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app = Flask(__name__)

    @app.route('/api/status', methods=['POST'])
    def status():
        data = request.json
        if data and 'status' in data:
            event_queue.put({'type': 'ai_status', 'status': data['status']})
            return jsonify({'success': True, 'status': data['status']})
        return jsonify({'error': 'Invalid payload'}), 400

    @app.route('/api/message', methods=['POST'])
    def message():
        data = request.json
        if data and 'message' in data:
            event_queue.put({'type': 'ai_message', 'message': data['message']})
            return jsonify({'success': True, 'message': data['message']})
        return jsonify({'error': 'Invalid payload'}), 400

    def run():
        app.run(host='127.0.0.1', port=3000, debug=False, use_reloader=False)

    server_thread = threading.Thread(target=run, daemon=True)
    server_thread.start()
