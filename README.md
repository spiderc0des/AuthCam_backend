# AuthCam Backend

Django REST API that powers [AuthCam](https://github.com/spiderc0des/AuthCam_expo), a mobile app that fights digital image manipulation by proving whether a photo is unaltered since capture.

## Related repo

- [`AuthCam_expo`](https://github.com/spiderc0des/AuthCam_expo) — the React Native/Expo mobile client. It calls this backend's `/api/v1/upload/` and `/api/v1/verify/` endpoints (plus `dj-rest-auth` for login/registration) to fingerprint photos at capture time and verify them later. This repo is the server the app talks to; the two are deployed and run separately but are useless without each other.

## How it works

1. **Upload** (`POST /api/v1/upload/`) — a user uploads a photo taken in the AuthCam app. The server embeds a unique UUID into the image's EXIF `UserComment` field, computes a SHA-256 hash of the resulting image, and stores `{user, uuid, hash_value, timestamp}` in the database (the original image itself is not kept). The processed image (with the embedded UUID) is returned to the app to save to the device.
2. **Verify** (`POST /api/v1/verify/`) — anyone can upload an image to check its authenticity. The server reads the UUID from the image's EXIF data, looks up the matching database record, and re-hashes the image:
   - Hash matches → `200 OK` with the original creator's username and capture timestamp (image is authentic/unmodified).
   - Hash differs → `412 Precondition Failed` (image has been modified since capture).
   - No matching UUID found → `404 Not Found`.

Authentication is via [dj-rest-auth](https://dj-rest-auth.readthedocs.io/) token auth (`django-allauth` for registration). Both endpoints require a logged-in user (`Authorization: Token <token>` header).

## Stack

- Django 5 + Django REST Framework
- `dj-rest-auth` / `django-allauth` for auth and registration
- Pillow + `piexif` for image EXIF handling and hashing
- SQLite for local dev, MySQL in production (switched via `DEBUG` setting)
- WhiteNoise for static file serving

## Project layout

- `authcam/` — Django project settings, root URL config
- `base/` — the app: `models.py` (`MediaInfo`), `views.py` (`upload`/`verify` endpoints), `serializers.py`, `urls.py`

## Running it locally

### Prerequisites

- Python 3.11
- `mysqlclient` requires MySQL client dev headers if you run in production mode (not needed for local SQLite dev)

### Setup

```bash
git clone git@github.com:spiderc0des/AuthCam_backend.git
cd AuthCam_backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure environment

Settings are loaded via `python-decouple` from a `.env` file in the project root. Create one:

```bash
# .env
KEY=some-django-secret-key
DEBUG=True
```

With `DEBUG=True` the app uses a local SQLite database (`db.sqlite3`) — no extra config needed.

For production-like runs (`DEBUG=False`), also set the MySQL connection details:

```bash
DB_NAME=authcam
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

### Migrate and run

```bash
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/`:

- `POST /register/` — create a user
- `POST /dj-rest-auth/login/` — log in, returns an auth token
- `POST /api/v1/upload/` — upload + fingerprint an image (auth required)
- `POST /api/v1/verify/` — verify an image's authenticity (auth required)
- `/admin/` — Django admin

### Pointing the mobile app at this server

The [AuthCam Expo app](https://github.com/spiderc0des/AuthCam_expo) currently points at a hosted deployment (`spidercodes.pythonanywhere.com`). To use a local backend instead, update the `baseURL`/endpoint URLs in the app's `screens/LoginScreen.js` and `screens/CameraScreen.js` to your local server's address (e.g. your machine's LAN IP if testing on a physical device, since `localhost` won't resolve from the phone).
