# Back-end-Development-Capstone

Django band website built from IBM's official capstone template. It integrates the separate Pictures (Flask) and Songs (Flask/MongoDB) APIs, with account registration, login/logout, concert browsing, per-user attendance and cancellation, and concert administration.

## Environment setup

Python 3.10+ is required; the container uses Python 3.11. Run `bash bin/setup.sh` and `source .venv/bin/activate`.

Create an untracked `.env` file with a fresh `DJANGO_SECRET_KEY`. Configure `SONGS_URL` and `PICTURES_URL`; local defaults are `http://127.0.0.1:5002` and `http://127.0.0.1:5001`.

```
python manage.py migrate
python manage.py seed_demo
python manage.py collectstatic --noinput
python manage.py runserver 127.0.0.1:8000
```

Optional environment variables `DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD` let `seed_demo` create the lab administrator. Existing users and edited concert records are preserved. Never commit this file or use a real personal password for the demo.

## Application behavior

Anonymous visitors can browse the band, songs, photographs and concerts. Signed-in users can RSVP, see their own attendance, and cancel a reservation. Mutations use POST and CSRF protection. Song lyrics open in a Bootstrap modal. Service timeouts and invalid responses show a temporary-unavailability message. Django admin can edit concert dates and details.

`Photo` and `Song` are unmanaged course model projections: their source data belongs to the microservices, so Django does not create duplicate tables. Concert and attendance records are persisted in SQLite through checked-in migrations.

## Validation

`python manage.py test --verbosity 2`

Seven tests cover authentication, unauthorized booking, duplicate RSVP prevention, isolated cancellation, invalid data, missing concerts, service responses/failure, and administrator edits. The final local integration also uses the live Pictures and Songs services with real MongoDB.

## Container and Kubernetes

```
docker build -t djangoserver .
```

The container runs as user 1001 with Gunicorn on port 8000 and WhiteNoise for static assets. Startup applies existing migrations and seeds missing demo records. Debug is disabled.

The supplied `deployment.yml` uses one replica and the `DJANGO_IMAGE` placeholder. Render it with `envsubst` before applying. Create `django-config` with `SONGS_URL`, `PICTURES_URL`, `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`, plus `django-secrets` with a generated secret key and lab administrator credentials. The Service maps port 8080 to 8000.

This course deployment uses SQLite on an `emptyDir`: data survives container restarts but resets when its pod is replaced. Production use would need persistent storage/database, service authentication and platform-specific hardening. The public APIs contain only synthetic course fixtures.
