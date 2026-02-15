Local development server

This small Flask app serves the previously downloaded JSON and static files so
you can run the frontend locally without the remote backend.

Run:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python local_server.py
```

Endpoints provided:
- `/` -> serves `remote_db_root.html`
- `/static/app.js` -> serves `remote_static_app.js`
- `/api/players` -> `remote_api_players.json`
- `/api/gameweeks` -> `remote_api_gameweeks.json`
- `/api/team_schedule/<gw>` -> placeholder JSON
- `/api/team_players/<team_id>` -> placeholder JSON
- `/api/game_schedule` (POST) -> placeholder response
