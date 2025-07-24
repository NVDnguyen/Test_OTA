# Pi App Project

## Setup Instructions

### 1. Run Backend with Docker

You can run the backend using Docker:

```fish
# Build and start the backend service
docker compose up --build
```

This will use the `docker-compose.yml` and `Dockerfile` in the project root to build and start the backend server.

### 2. Run Backend Manually

Alternatively, you can run the backend directly with Python:

```fish
python -m backend.app
```

#### Backend Configuration
- The backend uses configuration from `backend/config.py`.
- Settings are loaded from environment variables and `.env` file (see `model_config` in config).
- Main environment variables:
  - `APP_ENV`: "development" or "production"
  - `MONGO_URI`: MongoDB connection string
  - `REDIS_URI`: Redis connection string
  - `JWT_SECRET_KEY`: JWT secret key
  - `VIETQR_WEBHOOK_SECRET_KEY`: VietQR webhook secret
  - `ADMIN_EMAIL`: Initial admin email
  - `VIETQR_BANK_BIN`, `VIETQR_ACCOUNT_NO`, `VIETQR_ACCOUNT_NAME`: VietQR payment config
  - `JWT_ACCESS_TOKEN_EXPIRES`, `JWT_REFRESH_TOKEN_EXPIRES`: Token expiration (set in code)
- Edit `backend/config.py` or set environment variables in a `.env` file in the backend directory.

### 3. Run QT Client App

#### Install requirements library
- `source .venv/bin/activate`
- `pip install -r requirements.txt`
- `brew install zbar`

To start the QT client application:

```fish
python -m qt_client.main
```

#### QT Client Configuration
- Configuration for the QT client is in `qt_client/config/settings.py`.
- Settings are loaded from environment variables and `.env` file in the `qt_client` directory.
- Main environment variables:
  - `API_BASE_URL`: Backend API endpoint
  - `SERIAL_PORT`: Serial device path
  - `SERIAL_BAUDRATE`: Serial communication speed
- Edit `qt_client/config/settings.py` or set environment variables in a `.env` file in the `qt_client` directory.

---

## Additional Notes
- Make sure you have Python 3.10+ installed.
- Install dependencies with:
  ```fish
  pip install -r requirements.txt
  ```
- For development, you may want to run backend and client in separate terminals.
- For any issues, check the respective config files for environment-specific settings.
