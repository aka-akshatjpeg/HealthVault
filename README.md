# HealthVault

HealthVault is a patient-centered health records project with a Flask web backend and an Expo/React Native mobile app.

## Project layout

- `backend/` — Flask application, routes, templates, and static assets
- `HealthVaultMobile/` — Expo mobile app

## Backend setup

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` and set a private `SECRET_KEY`. Add a `GEMINI_API_KEY` only if you want to use the AI features. Start the server with:

```powershell
python app.py
```

This starts the Flask development server on port `5000`. Database tables are created automatically on startup. The local SQLite database and uploaded files stay on your machine.

## Mobile setup

```powershell
cd HealthVaultMobile
Copy-Item .env.example .env.local
npm ci
npm start
```

The example URL targets the Android emulator. For a physical phone, set `EXPO_PUBLIC_API_URL` in `.env.local` to your computer's LAN address, with port `5000`. Restart Expo after changing it.

## Configuration and data

Keep API keys, secret values, real patient information, local databases, and uploaded documents out of Git. The `.env.example` files contain placeholders and can be committed safely. The included server is for local development; use a production WSGI server and deployment settings before hosting it publicly.

## License

No license is included. Ask the author before reusing or redistributing this project.

