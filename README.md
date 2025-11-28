# Super SIM Heatmap

A FastAPI + Leaflet application for visualizing Kore Super SIM connection events (https://docs.korewireless.com/en-us/developers/event-streams) in real time. The backend ingests webhook notifications and persists raw payloads in SQLite; the frontend renders a dual-layer heatmap (online vs offline devices), a device list, and a timeline slider that shows how fleets transition throughout the day.


## Highlights

| Feature | Description |
| --- | --- |
| **Webhook ingestion** | `POST /webhooks/supersim` accepts Kore Super SIM stream payloads, validates them with Pydantic, and stores the raw JSON for traceability. |
| **Device timeline** | A timeline slider (00:00–23:59) filters events to a single day. Unique ICCIDs are counted as *online* or *offline* based on their latest state before the selected time. |
| **Heatmap layers** | Online (green) and offline (red) sessions render as separate Leaflet heat layers with independent toggles and a “Show All” control to fit the current clusters. |
| **Events panel** | The sidebar lists the newest device events (paginated 50 at a time) with SIM name/ICCID, tower, network, and status. Clicking an entry pans the map to the tower location. |
| **Seeder utility** | `app/demo/utils/seed_events.py` synthesizes realistic start/update/end sequences across Naples, Toronto, São Paulo, Lisbon, Shanghai, Cape Town, and Sydney with per-device controls. |
| **SQLite by default** | Works out-of-the-box with `events.db` but supports any SQLModel-compatible database via `DATABASE_URL`. |

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 to view the map.

### Run with Docker

Build the image and run it directly:

```bash
docker build -t supersim-heatmap .
docker run --rm -p 8000:8000 \
  -e DATABASE_URL=sqlite:////data/events.db \
  -v supersim_data:/data \
  supersim-heatmap
```

Or use docker-compose (recommended locally for persistence):

```bash
docker compose up --build
```

Then open http://127.0.0.1:8000. The SQLite database is persisted in a named volume (`supersim_data`).

### Configure the database (optional)

Set `DATABASE_URL` (e.g. `postgresql+psycopg://user:pass@localhost/supersim`) before starting Uvicorn. SQLModel handles migrations at startup.
When running via Docker Compose, a default `DATABASE_URL=sqlite:////data/events.db` is provided and mounted to a volume.

## Ingesting Real Events

Point the Super SIM webhook to `https://<your-host>/webhooks/supersim`. During development, expose your localhost via ngrok or Cloudflare Tunnel:

```bash
ngrok http 8000
# configure Kore webhook to https://<random>.ngrok.io/webhooks/supersim
```

## Demo Data Seeder

Use the helper script to populate the map with synthetic devices. The script simulates coherent sessions (START → UPDATE → END) per ICCID so the timeline accurately reflects online/offline states.

Examples:

```bash
# 50 devices in Naples, ~550 sessions total
.venv/bin/python app/demo/utils/seed_events.py --region naples --devices 50 --count 550

# 30 devices in every region, 5 sessions each
for region in naples toronto saopaulo lisbon shanghai capetown sydney; do
  .venv/bin/python app/demo/utils/seed_events.py --region "$region" --devices 30 --sessions-per-device 5
done
```

Key options:

| Flag | Default | Meaning |
| --- | --- | --- |
| `--region` | *all regions* | Restrict sessions to a single city (Naples, Toronto, etc.). |
| `--devices` | 10 | Number of unique ICCIDs/devices to generate (per region). |
| `--count` | 60 | Total sessions; distributed across devices if `--sessions-per-device` is not set. |
| `--sessions-per-device` | *none* | Exact number of sessions per device (overrides `--count`). |
| `--url` | http://127.0.0.1:8000/webhooks/supersim | Target webhook endpoint. |

Each seeded device gets a derived ICCID (e.g., `Digital Matter Barra GPS 12` with `898830790353775161311`), so the timeline and stats treat every device uniquely.

## Manual Event Testing

You can push a single event into the database with curl. The webhook expects a JSON array of events (even if you send just one).

Prerequisites:
- Start the server locally (or with Docker) so http://127.0.0.1:8000 is reachable.
- Endpoint: POST /webhooks/supersim

Examples for the three key event types:

1) Session Started
```bash
curl -X POST http://127.0.0.1:8000/webhooks/supersim \
  -H "Content-Type: application/json" \
  -d '[{"data":{"apn":"super","imei":"353785726123176","imsi":"732123206640719","network":{"mcc":"310","mnc":"170","sid":"HWb90542dc0d8b4276a694d0fe5c794168","iso_country":"US","friendly_name":"AT&T"},"sim_sid":"HS7319340e9486db1faba1eb2790e6ef03","location":{"lac":"602","lat":26.2721,"lon":-81.8090,"cell_id":"40026625"},"rat_type":"4G LTE","event_sid":"EZ123","fleet_sid":"HF123","sim_iccid":"89883070000044236204","timestamp":"2025-11-26T09:05:44Z","event_type":"com.twilio.iot.supersim.connection.data-session.started","ip_address":"100.65.109.189","account_sid":"AC123","sim_unique_name":"Digital Matter Barra GPS","data_session_sid":"PI123","data_session_start_time":"2025-11-26T09:05:44Z"},"id":"EZ123","time":"2025-11-26T09:05:44Z","type":"com.twilio.iot.supersim.connection.data-session.started","source":"kore-events","dataschema":"https://events-schemas.korewireless.com/SuperSim.ConnectionEvent/2","specversion":"2.0","datacontenttype":"application/json"}]'
# => {"stored": 1}
```

2) Session Updated
```bash
curl -X POST http://127.0.0.1:8000/webhooks/supersim \
  -H "Content-Type: application/json" \
  -d '[{"data":{"apn":"super","imei":"353785726123176","imsi":"732123206640719","network":{"mcc":"310","mnc":"170","sid":"HWb90542dc0d8b4276a694d0fe5c794168","iso_country":"US","friendly_name":"AT&T"},"sim_sid":"HS7319340e9486db1faba1eb2790e6ef03","location":{"lac":"602","lat":26.2721,"lon":-81.8090,"cell_id":"40026625"},"rat_type":"4G LTE","event_sid":"EZ124","fleet_sid":"HF123","sim_iccid":"89883070000044236204","timestamp":"2025-11-26T09:15:44Z","data_total":4096,"event_type":"com.twilio.iot.supersim.connection.data-session.updated","ip_address":"100.66.10.142","account_sid":"AC123","data_upload":2048,"data_download":2048,"sim_unique_name":"Digital Matter Barra GPS","data_session_sid":"PI123","data_session_start_time":"2025-11-26T09:05:44Z","data_session_data_total":4096,"data_session_update_start_time":"2025-11-26T09:10:44Z","data_session_update_end_time":"2025-11-26T09:15:44Z"},"id":"EZ124","time":"2025-11-26T09:15:44Z","type":"com.twilio.iot.supersim.connection.data-session.updated","source":"kore-events","dataschema":"https://events-schemas.korewireless.com/SuperSim.ConnectionEvent/2","specversion":"2.0","datacontenttype":"application/json"}]'
# => {"stored": 1}
```

3) Session Ended
```bash
curl -X POST http://127.0.0.1:8000/webhooks/supersim \
  -H "Content-Type: application/json" \
  -d '[{"data":{"apn":"super","imei":"353785726123176","imsi":"732123206640719","network":{"mcc":"310","mnc":"170","sid":"HWb90542dc0d8b4276a694d0fe5c794168","iso_country":"US","friendly_name":"AT&T"},"sim_sid":"HS7319340e9486db1faba1eb2790e6ef03","location":{"lac":"602","lat":26.2721,"lon":-81.8090,"cell_id":"40026625"},"rat_type":"4G LTE","event_sid":"EZ125","fleet_sid":"HF123","sim_iccid":"89883070000044236204","timestamp":"2025-11-26T09:25:44Z","data_total":8192,"event_type":"com.twilio.iot.supersim.connection.data-session.ended","ip_address":"100.67.17.62","account_sid":"AC123","data_upload":4096,"data_download":4096,"sim_unique_name":"Digital Matter Barra GPS","data_session_sid":"PI123","data_session_start_time":"2025-11-26T09:05:44Z","data_session_end_time":"2025-11-26T09:25:44Z","data_session_update_end_time":"2025-11-26T09:20:44Z"},"id":"EZ125","time":"2025-11-26T09:25:44Z","type":"com.twilio.iot.supersim.connection.data-session.ended","source":"kore-events","dataschema":"https://events-schemas.korewireless.com/SuperSim.ConnectionEvent/2","specversion":"2.0","datacontenttype":"application/json"}]'
# => {"stored": 1}
```

Verify:
- Open http://127.0.0.1:8000 and refresh; the event list and heatmap should reflect the new data.
- Or check raw JSON: http://127.0.0.1:8000/events?limit=5

Notes:
- If you run via Docker Compose, the host-side curl to http://127.0.0.1:8000 works as shown.
- On Windows PowerShell, prefer using double quotes and escape inner quotes, or place the JSON body in a file and use `-d @payload.json`.
## Web UI Overview

1. **Device sidebar** – Latest events (50 at a time) with “Load More” button. Clicking pans the map to the tower location.
2. **Heatmap controls** – Toggle Online/Offline layers and click “Show All” to refit the map.
3. **Timeline** – Drag to any time of day; counts update based on the most recent event per ICCID before that time.
4. **Stats** – Displays unique devices online/offline at the selected time.

## Project Layout

```
.
├── app/                 # FastAPI application (routers, models, schemas)
│   └── demo/
│       └── utils/       # Seeder and demo helpers (seed_events.py)
├── templates/           # Leaflet UI (Jinja2)
├── static/              # Leaflet assets, CSS tweaks
├── docs/                # Screenshots
├── requirements.txt     # Python dependencies
└── README.md
```

## Contributing

Issues and PRs are welcome! Ideas:

- Add auth or API keys for the webhook.
- Support Postgres/PostGIS out-of-the-box.
- Implement historical playback (scrub across multiple days).
- Export filtered events as CSV/GeoJSON.

---

Built with ❤️ using OpenAI Codex. Let us know how you’re using it! 
