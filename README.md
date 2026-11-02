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

## Firebase sign-in

See [FIREBASE_AUTH_SETUP.md](FIREBASE_AUTH_SETUP.md) for the Firebase Console, web, mobile, and development-build setup steps.

## Configuration and data

Keep API keys, secret values, real patient information, local databases, and uploaded documents out of Git. The `.env.example` files contain placeholders and can be committed safely. The included server is for local development; use a production WSGI server and deployment settings before hosting it publicly.

`DATABASE_URL` can optionally point Flask-SQLAlchemy at another database; SQLite remains the default. Startup creates missing tables and adds missing organization/provider profile columns without dropping existing rows. Back up an existing database before deploying application changes. This project does not yet have a versioned migration history for every schema change.

`DEMO_MODE` defaults to `false`. Set it to `true` only for local demonstrations: simulated login and Aadhaar OTPs are shown to the client. Real OTP delivery and Aadhaar verification are not integrated, so those sign-in/verification flows return an unavailable response with demo mode disabled.

Set `PUBLIC_BASE_URL` to the deployed HTTPS origin when hosting the app so generated HealthVault QR codes link to the right site.

## License

No license is included. Ask the author before reusing or redistributing this project.

