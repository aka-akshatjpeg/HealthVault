# HealthVault

HealthVault is a patient-centered health records application with a Flask web backend and an Expo/React Native mobile app. It is intended to help patients organize health information and share selected records with healthcare providers.

## Project layout

- `backend/` — Flask application, routes, templates, and static assets
- `HealthVaultMobile/` — Expo mobile app

## Backend setup

```bash
cd backend
python -m venv .venv
```

Activate the environment, install dependencies, create a local `backend/.env` from your own configuration, then run:

```bash
pip install -r requirements.txt
python app.py
```

Keep secret keys and API credentials in the local environment file. Never commit real patient records or uploaded documents.

## Mobile setup

```bash
cd HealthVaultMobile
npm install
npm start
```

Configure service endpoints and any required credentials for your own development environment. Do not commit local environment files or production credentials.

## License

No license is included. Ask the author before reusing or redistributing this project.

