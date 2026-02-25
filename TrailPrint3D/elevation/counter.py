"""API request counter — daily (OpenTopoData) and monthly (OpenElevation) tracking."""

import json
import os
from datetime import date, datetime

import bpy  # type: ignore

counter_file = os.path.join(bpy.utils.user_resource('CONFIG'), "api_request_counter.json")


def load_counter():
    """Load counters → (count_otd, date_otd, count_oe, date_oe)."""
    if os.path.exists(counter_file):
        try:
            with open(counter_file, "r") as f:
                data = json.load(f)
                return (
                    data.get("count_openTopodata", 0),
                    data.get("date_openTopoData", ""),
                    data.get("count_openElevation", 0),
                    data.get("date_openElevation", ""),
                )
        except (OSError, json.JSONDecodeError, KeyError):
            return 0, "", 0, ""
    return 0, "", 0, ""


def save_counter(count_otd, date_otd, count_oe, date_oe):
    """Persist counter state to disk."""
    with open(counter_file, "w") as f:
        json.dump({
            "count_openTopodata": count_otd,
            "date_openTopoData": date_otd,
            "count_openElevation": count_oe,
            "date_openElevation": date_oe,
        }, f)


def update_request_counter(api: int = 0):
    """Increment and return (count_otd, count_oe)."""
    today_date = date.today().isoformat()
    today_month = date.today().month

    count_otd, date_otd, count_oe, date_oe = load_counter()

    if date_otd != today_date:
        count_otd = 0
    if date_oe != today_month:
        count_oe = 0

    if api == 0:
        count_otd += 1
    elif api == 1:
        count_oe += 1

    save_counter(count_otd, today_date, count_oe, today_month)
    return count_otd, count_oe


def send_api_request(addition: str = "", api: int = 0, dataset: str = ""):
    """Log a request and print progress."""
    request_count = update_request_counter(api)
    now = datetime.now()
    if api == 0:
        print(f"{now.hour:02d}:{now.minute:02d} | Fetching: {addition} | API Usage: {request_count} | {dataset}")
    elif api == 1:
        print(f"{now.hour:02d}:{now.minute:02d} | Fetching: {addition} | API Usage: {request_count}")
    elif api == 2:
        print(f"{now.hour:02d}:{now.minute:02d} | Fetching API")
