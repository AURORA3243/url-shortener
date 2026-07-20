# URL Shortener

A containerized URL shortening service with click tracking.

## What it does
- Shorten any long URL into a short code
- Redirect short URLs to original destination
- Track click count for every short URL
- View all shortened URLs with stats

## Tech Stack
- Python + Flask (API)
- PostgreSQL (URL storage + click tracking)
- Podman + Compose (containerization)
- Nginx (reverse proxy on AWS)
- AWS EC2 (deployment)

## Run it yourself
```bash
git clone https://github.com/AURORA3243/url-shortener
cd url-shortener
podman-compose up
```
Then open http://localhost:5001

## API Endpoints
- GET  /         — web UI
- POST /api/shorten — shorten a URL
- GET  /api/urls    — list all URLs
- GET  /s/<code>    — redirect to original URL
