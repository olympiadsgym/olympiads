# Static files on Vercel (Django + WhiteNoise)

## Why `staticfiles.json` matters
This project uses `whitenoise.storage.CompressedManifestStaticFilesStorage`.
That storage expects a `staticfiles.json` manifest to exist (WhiteNoise uses it to map original filenames to hashed/compressed versions).

## What to ensure
- `STATIC_ROOT` points to a directory that is included in the Vercel static build output.
- `python manage.py collectstatic` is executed during the Vercel build (via `build_files.sh`).

## Current approach
- `build_files.sh` runs:
  - `python manage.py migrate --noinput`
  - `python manage.py collectstatic --noinput`
- `vercel.json` routes `/static/(.*)` to Vercel-served `staticfiles/**`.

If CSS/JS are missing on Vercel, the first thing to verify is that `staticfiles/staticfiles.json` exists after `collectstatic`.

