# SpoolSense

Track your 3D printing filament inventory, print jobs, orders, and costs — all in one place, running on your own hardware.

**Want to try it first?** [Live demo at app.spoolsense.co](https://app.spoolsense.co) — login with `demo@demo.com` / `demo` (resets every 30 minutes).

## Features

- **Spool inventory** — track filament by type, manufacturer, color, weight, and cost
- **Print job logging** — log print jobs with filament usage and time
- **Orders & customers** — manage customer orders with full cost breakdown
- **Hardware tracking** — track printers, parts, and accessories
- **Projects** — organize print files and estimate costs
- **Cost estimation** — calculate per-print cost including electricity, time, and depreciation
- **Webhook notifications** — order due dates, low stock alerts, status changes
- **Dark mode** — easy on the eyes during late-night print sessions

## Quick Start

Create a `docker-compose.yml`:

```yaml
services:
  spoolsense:
    image: jaconah/spoolsense:latest
    container_name: spoolsense
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

Then start it:

```bash
docker compose up -d
```

SpoolSense will be available at `http://your-server-ip:8000`. No configuration needed to get running.

### Set your password

On first run, the default password is **`changeme`**. Log in immediately and go to **Profile → Change Password**.

### (Optional) Custom domain / reverse proxy

If you're putting SpoolSense behind nginx or Caddy with a domain name, create a `.env` file next to your `docker-compose.yml` and set `FRONTEND_URL` so CORS is locked down:

```ini
FRONTEND_URL=https://yourdomain.com
```

## Upgrading

```bash
docker compose pull
docker compose up -d
```

## SpoolSense Cloud

A fully managed hosted version is coming soon at [app.spoolsense.co](https://app.spoolsense.co) — same features, zero maintenance.

---

If SpoolSense saves you time, consider buying me a coffee: [ko-fi.com/jaconah](https://ko-fi.com/jaconah)
