from flask import Flask, jsonify, request, send_file, abort
import json
import os

app = Flask(__name__)

ROOT = os.path.dirname(os.path.abspath(__file__))


def _read_json(fname):
    path = os.path.join(ROOT, fname)
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


@app.route('/')
def index():
    path = os.path.join(ROOT, 'remote_db_root.html')
    if not os.path.exists(path):
        return "Index file not found", 404
    return send_file(path)


@app.route('/static/<path:filename>')
def static_files(filename):
    # Serve the downloaded app.js when requested as /static/app.js
    if filename == 'app.js' and os.path.exists(os.path.join(ROOT, 'remote_static_app.js')):
        return send_file(os.path.join(ROOT, 'remote_static_app.js'))
    # Fallback: try to serve from a `static` folder if present
    static_path = os.path.join(ROOT, 'static', filename)
    if os.path.exists(static_path):
        return send_file(static_path)
    abort(404)


@app.route('/api/players')
def api_players():
    data = _read_json('remote_api_players.json')
    if data is None:
        return jsonify([])
    return jsonify(data)


@app.route('/api/gameweeks')
def api_gameweeks():
    data = _read_json('remote_api_gameweeks.json')
    if data is None:
        return jsonify([])
    return jsonify(data)


@app.route('/api/team_schedule/<int:gameweek>')
def api_team_schedule(gameweek):
    # Minimal placeholder structure compatible with frontend expectations
    return jsonify({
        "gameweek": gameweek,
        "date_range": "N/A",
        "teams": []
    })


@app.route('/api/team_players/<int:team_id>')
def api_team_players(team_id):
    # Return empty lists; frontend will handle absence of players
    return jsonify({"backcourt": [], "frontcourt": []})


@app.route('/api/game_schedule', methods=['POST'])
def api_game_schedule():
    # Accept posted roster and return a minimal games_by_day structure
    body = request.get_json(silent=True) or {}
    return jsonify({"games_by_day": {}})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
