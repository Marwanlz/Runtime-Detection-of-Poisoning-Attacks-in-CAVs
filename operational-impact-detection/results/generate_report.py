import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

CENTRAL_EVENTS_FILE = "../edge_siem/logs/received_events.json"
CORRELATED_ALERTS_FILE = "../edge_siem/logs/correlated_alerts.json"
OUTPUT_PDF = "siem_report.pdf"


def load_json_file(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default
    return default


def fit_text(c, text, x, y, max_width, font_name="Helvetica", font_size=10):
    text = str(text)
    if stringWidth(text, font_name, font_size) <= max_width:
        c.setFont(font_name, font_size)
        c.drawString(x, y, text)
        return

    shortened = text
    while shortened and stringWidth(shortened + "...", font_name, font_size) > max_width:
        shortened = shortened[:-1]

    c.setFont(font_name, font_size)
    c.drawString(x, y, shortened + "...")


def draw_section_title(c, title, x, y):
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x, y, title)
    return y - 8 * mm


def draw_key_value(c, key, value, x, y, page_width):
    KEY_COL_WIDTH = 70 * mm
    VALUE_X = x + KEY_COL_WIDTH
    RIGHT_MARGIN = 20 * mm

    if isinstance(value, list):
        value = ", ".join(str(v) for v in value)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, f"{key}:")

    fit_text(
        c,
        value,
        VALUE_X,
        y,
        page_width - VALUE_X - RIGHT_MARGIN
    )

    return y - 6 * mm


def ensure_space(c, y, needed_height):
    if y < needed_height:
        c.showPage()
        return A4[1] - 20 * mm
    return y


def detect_mode(received_events):
    if not received_events:
        return "UNKNOWN"

    modes = [event.get("mode", "").lower() for event in received_events if event.get("mode")]

    if not modes:
        return "UNKNOWN"

    if all(m == "baseline" for m in modes):
        return "BASELINE"

    if all(m == "hybrid" for m in modes):
        return "HYBRID"

    return "MIXED"


def build_events_per_vehicle(received_events):
    events_per_vehicle = {}
    for event in received_events:
        vehicle_id = event.get("vehicle_id", "unknown")
        events_per_vehicle[vehicle_id] = events_per_vehicle.get(vehicle_id, 0) + 1
    return events_per_vehicle


def build_events_per_type(received_events):
    events_per_type = {}
    for event in received_events:
        event_type = event.get("event_type", "unknown")
        events_per_type[event_type] = events_per_type.get(event_type, 0) + 1
    return events_per_type


def generate_report():
    received_events = load_json_file(CENTRAL_EVENTS_FILE, [])
    correlated_alerts = load_json_file(CORRELATED_ALERTS_FILE, [])

    mode = detect_mode(received_events)
    events_per_vehicle = build_events_per_vehicle(received_events)
    events_per_type = build_events_per_type(received_events)
    events_forwarded = len(received_events)

    c = canvas.Canvas(OUTPUT_PDF, pagesize=A4)
    page_width, page_height = A4
    x = 20 * mm
    y = page_height - 20 * mm

    c.setTitle("Hybrid SIEM Monitoring Report")

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "Hybrid SIEM Monitoring Report")
    y -= 10 * mm

    c.setFont("Helvetica", 10)
    c.drawString(x, y, f"generated_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 10 * mm

    y = draw_section_title(c, "execution_summary", x, y)
    y = draw_key_value(c, "mode", mode, x, y, page_width)
    y = draw_key_value(c, "events_forwarded", events_forwarded, x, y, page_width)
    y = draw_key_value(c, "correlated_alerts_count", len(correlated_alerts), x, y, page_width)

    y -= 4 * mm
    y = draw_section_title(c, "events_per_vehicle", x, y)
    for vehicle, count in sorted(events_per_vehicle.items()):
        y = ensure_space(c, y, 25 * mm)
        y = draw_key_value(c, vehicle, count, x, y, page_width)

    y -= 4 * mm
    y = draw_section_title(c, "events_per_type", x, y)
    for event_type, count in sorted(events_per_type.items()):
        y = ensure_space(c, y, 25 * mm)
        y = draw_key_value(c, event_type, count, x, y, page_width)

    y -= 4 * mm
    y = draw_section_title(c, "received_events", x, y)

    if not received_events:
        y = draw_key_value(c, "status", "none", x, y, page_width)
    else:
        for idx, event in enumerate(received_events, start=1):
            y = ensure_space(c, y, 60 * mm)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x, y, f"event_{idx}")
            y -= 6 * mm

            for key in [
                "event_id",
                "vehicle_id",
                "timestamp",
                "event_type",
                "priority",
                "rule_flag",
                "ai_anomaly",
                "anomaly_score",
            ]:
                if key in event:
                    y = draw_key_value(c, key, event[key], x + 5 * mm, y, page_width)

            y -= 3 * mm

    y = ensure_space(c, y, 40 * mm)
    y = draw_section_title(c, "correlated_alerts", x, y)

    if not correlated_alerts:
        y = draw_key_value(c, "status", "none", x, y, page_width)
    else:
        for idx, alert in enumerate(correlated_alerts, start=1):
            y = ensure_space(c, y, 55 * mm)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x, y, f"alert_{idx}")
            y -= 6 * mm

            for key in [
                "alert_type",
                "event_type",
                "vehicles",
                "event_ids",
                "event_count",
                "time_window_seconds",
                "first_timestamp",
                "last_timestamp",
            ]:
                if key not in alert:
                    continue

                if key == "event_ids":
                    y = draw_key_value(c, "event_ids", "", x + 5 * mm, y, page_width)

                    for eid in alert["event_ids"]:
                        y = ensure_space(c, y, 20 * mm)
                        c.setFont("Helvetica", 10)
                        c.drawString(x + 15 * mm, y, eid)
                        y -= 5 * mm

                else:
                    y = draw_key_value(c, key, alert[key], x + 5 * mm, y, page_width)

            y -= 3 * mm

    c.save()
    print(f"Report generated: {OUTPUT_PDF}")


if __name__ == "__main__":
    generate_report()