"""Seed the webhook endpoint with randomized Super SIM events."""
from __future__ import annotations
import argparse
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterator, List, Sequence
import httpx

REGIONS = {
    "naples": ((26.1415, 26.1430), (-81.7955, -81.7935)),
    "toronto": ((43.65, 43.70), (-79.63, -79.38)),
    "saopaulo": ((-23.55, -23.5), (-46.65, -46.6)),
    "lisbon": ((38.70, 38.74), (-9.17, -9.12)),
    "shanghai": ((30.67, 31.88), (120.87, 122.20)),
    "capetown": ((-33.95, -33.90), (18.35, 18.50)),
    "sydney": ((-33.90, -33.85), (151.15, 151.25)),
}

REGION_NETWORKS = {
    "naples": [
        ("AT&T", "US", "310", "170"),
        ("Verizon Wireless", "US", "310", "012"),
    ],
    "toronto": [
        ("Rogers Communications", "CA", "302", "720"),
        ("Telus Mobility", "CA", "302", "220"),
    ],
    "saopaulo": [
        ("Telefônica Brasil S.A", "BR", "724", "06"),
        ("TIM", "BR", "724", "05"),
    ],
    "lisbon": [
        ("Vodafone Portugal", "PT", "268", "91"),
        ("Telecomunicações Móveis Nacionais", "PT", "268", "06"),
    ],
    "shanghai": [
        ("China Telecom", "CN", "460", "03"),
        ("China Mobile", "CN", "460", "00"),

    ],
    "capetown": [
        ("Vodacom", "ZA", "655", "01"),
        ("MTN Group", "ZA", "655", "10"),
    ],
    "sydney": [
        ("Vodafone Australia", "AU", "505", "03"),
        ("Telstra", "AU", "505", "01"),
    ],
}

DEVICE_INFO = [
    ("Digital Matter Barra GPS", "898830790353775161300"),
    ("Queclink GL300", "898830790353775161400"),
    ("Geometris OBDII", "898830790353775161500"),
    ("Suntech ST4515", "898830790353775161600"),
    ("Ruptela Plug5", "898830790353775161700"),
]

def random_lat_lon(region: str) -> tuple[float, float]:
    lat_range, lon_range = REGIONS[region]
    return (
        random.uniform(*lat_range),
        random.uniform(*lon_range),
    )


def random_string(prefix: str, length: int = 8) -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}{suffix}"


def choose_network(region: str) -> tuple[str, str, str, str]:
    networks = REGION_NETWORKS.get(region)
    if not networks:
        raise ValueError(f"Unknown region '{region}' for network selection")
    return random.choice(networks)


def build_session(
    region: str,
    *,
    device_name: str,
    iccid: str,
    sim_sid: str,
    imei: str,
    imsi: str,
    day_start: datetime,
) -> List[Dict]:
    lat, lon = random_lat_lon(region)
    network_name, iso_country, mcc, mnc = choose_network(region)
    sim_display_name = device_name

    minutes_in_day = 24 * 60
    update_gap = random.randint(5, 20)
    end_gap = random.randint(5, 20)
    max_offset = minutes_in_day - (update_gap + end_gap + 1)
    start_offset = random.randint(0, max_offset)
    start_time = day_start + timedelta(minutes=start_offset)
    update_time = start_time + timedelta(minutes=update_gap)
    end_time = update_time + timedelta(minutes=end_gap)

    def make_payload(
        event_type: str,
        timestamp: datetime,
        *,
        session_end: datetime | None,
        update_window: timedelta,
    ) -> Dict:
        update_start = timestamp - update_window
        data_total = random.randint(500, 50_000)
        data_upload = random.randint(100, data_total)
        data_download = random.randint(100, data_total)
        payload = {
            "data": {
                "apn": "super",
                "imei": imei,
                "imsi": imsi,
                "network": {
                    "mcc": mcc,
                    "mnc": mnc,
                    "sid": random_string("HWb"),
                    "iso_country": iso_country,
                    "friendly_name": network_name,
                },
                "sim_sid": sim_sid,
                "location": {
                    "lac": str(random.randint(100, 999)),
                    "lat": round(lat, 5),
                    "lon": round(lon, 5),
                    "cell_id": str(random.randint(10_000_000, 99_999_999)),
                },
                "rat_type": random.choice(["4G LTE", "LTE Cat-M", "NB-IoT"]),
                "event_sid": random_string("EZ"),
                "fleet_sid": random_string("HF"),
                "sim_iccid": iccid,
                "timestamp": timestamp.isoformat(),
                "data_total": data_total,
                "event_type": event_type,
                "ip_address": f"100.{random.randint(64, 127)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
                "account_sid": random_string("AC"),
                "data_upload": data_upload,
                "data_download": data_download,
                "sim_unique_name": sim_display_name,
                "data_session_sid": random_string("PI"),
                "data_session_start_time": start_time.isoformat(),
                "data_session_end_time": session_end.isoformat() if session_end else None,
                "data_session_data_total": data_total,
                "data_session_data_upload": data_upload,
                "data_session_data_download": data_download,
                "data_session_update_start_time": update_start.isoformat(),
                "data_session_update_end_time": timestamp.isoformat(),
            },
            "id": random_string("EZ"),
            "time": timestamp.isoformat(),
            "type": event_type,
            "source": "kore-events",
            "dataschema": "https://events-schemas.korewireless.com/SuperSim.ConnectionEvent/2",
            "specversion": "2.0",
            "datacontenttype": "application/json",
        }
        return payload

    events = [
        make_payload(
            "com.twilio.iot.supersim.connection.data-session.started",
            start_time,
            session_end=None,
            update_window=timedelta(seconds=5),
        ),
        make_payload(
            "com.twilio.iot.supersim.connection.data-session.updated",
            update_time,
            session_end=None,
            update_window=timedelta(seconds=30),
        ),
        make_payload(
            "com.twilio.iot.supersim.connection.data-session.ended",
            end_time,
            session_end=end_time,
            update_window=timedelta(seconds=30),
        ),
    ]
    return events


def generate_device_profiles(device_count: int) -> List[Dict]:
    profiles: List[Dict] = []
    width = len(DEVICE_INFO[0][1])
    for idx in range(device_count):
        base_name, base_iccid = DEVICE_INFO[idx % len(DEVICE_INFO)]
        suffix = f" {idx + 1}"
        derived_iccid = str(int(base_iccid) + idx).zfill(width)
        profiles.append(
            {
                "name": f"{base_name}{suffix}",
                "iccid": derived_iccid,
                "sim_sid": random_string("HS"),
                "imei": f"35{random.randint(10**13, 10**14 - 1)}",
                "imsi": f"732{random.randint(10**10, 10**11 - 1)}",
            }
        )
    return profiles


def distribute_sessions(total_sessions: int, device_count: int) -> List[int]:
    if device_count == 0:
        return []
    base = total_sessions // device_count
    remainder = total_sessions % device_count
    return [base + (1 if idx < remainder else 0) for idx in range(device_count)]


def chunked(iterable: Sequence, size: int) -> Iterator[List]:
    for idx in range(0, len(iterable), size):
        yield list(iterable[idx : idx + size])


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Super SIM webhook with random events")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000/webhooks/supersim",
        help="Webhook endpoint to POST sample events to",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=60,
        help="Total number of sessions to generate (ignored when --sessions-per-device is provided)",
    )
    parser.add_argument(
        "--region",
        choices=REGIONS.keys(),
        help="Restrict all sessions to a single region/city",
    )
    parser.add_argument(
        "--devices",
        type=int,
        default=10,
        help="Number of devices (unique ICCIDs) to simulate",
    )
    parser.add_argument(
        "--sessions-per-device",
        type=int,
        help="Number of sessions per device (overrides --count)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Batch size when posting events",
    )
    parser.add_argument(
        "--source",
        type=str,
        default="kore-events",
        help="Value to set in the root 'source' field for each emitted event (used to identify demo runs)",
    )
    args = parser.parse_args()

    target_regions = [args.region] if args.region else list(REGIONS.keys())
    day_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    if args.sessions_per_device:
        region_session_targets = [args.sessions_per_device * args.devices] * len(target_regions)
    else:
        base = args.count // len(target_regions)
        remainder = args.count % len(target_regions)
        region_session_targets = [base + (1 if idx < remainder else 0) for idx in range(len(target_regions))]

    events: List[Dict] = []
    region_summary = []

    for idx, region in enumerate(target_regions):
        profiles = generate_device_profiles(args.devices)
        if args.sessions_per_device:
            distribution = [args.sessions_per_device] * len(profiles)
        else:
            distribution = distribute_sessions(region_session_targets[idx], len(profiles))
        sessions_this_region = 0
        for profile, session_count in zip(profiles, distribution):
            for _ in range(session_count):
                events.extend(
                    build_session(
                        region,
                        device_name=profile["name"],
                        iccid=profile["iccid"],
                        sim_sid=profile["sim_sid"],
                        imei=profile["imei"],
                        imsi=profile["imsi"],
                        day_start=day_start,
                    )
                )
                sessions_this_region += 1
        region_summary.append(f"{region}: {sessions_this_region} sessions")

    total_sent = 0
    with httpx.Client(timeout=10) as client:
        for chunk in chunked(events, args.batch_size):
            # Override the top-level 'source' for demo identification if provided
            payload = [
                {
                    **evt,
                    "source": args.source or evt.get("source", "kore-events"),
                }
                for evt in chunk
            ]
            response = client.post(args.url, json=payload)
            response.raise_for_status()
            total_sent += len(chunk)
            print(f"Posted batch of {len(chunk)} events -> {response.json()}")

    print("Done.")
    print("Regions:", ", ".join(region_summary))
    print(f"Total events posted: {total_sent}")


if __name__ == "__main__":
    main()
