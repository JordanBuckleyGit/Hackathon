from flask import Flask, render_template, session, redirect, url_for, g, request
from database import get_db, close_db
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LogFilterForm
from functools import wraps
from collections import OrderedDict, Counter
import datetime
import os

app = Flask(__name__)
app.teardown_appcontext(close_db)
app.config["SECRET_KEY"] = "jsonDerulo"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = "static/images"
Session(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    form = LogFilterForm()
    db = get_db()
    query = "SELECT * FROM logs"
    filters = []
    params = []

    if form.validate_on_submit():
        if form.ip_address.data:
            filters.append("ip_address LIKE ?")
            params.append(f"%{form.ip_address.data}%")
        if form.status_code.data:
            filters.append("status_code = ?")
            params.append(form.status_code.data)
        if form.method.data:
            filters.append("request LIKE ?")
            params.append(f"{form.method.data} %")

    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY id ASC"

    log_entries = db.execute(query, params).fetchall()

    total_requests = db.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    avg_bytes = db.execute("SELECT AVG(bytes_sent) FROM logs").fetchone()[0]
    most_common_status = db.execute(
            "SELECT status_code, COUNT(*) as cnt FROM logs GROUP BY status_code ORDER BY cnt DESC LIMIT 1"
        ).fetchone()
    most_common_ip = db.execute(
        "SELECT ip_address, COUNT(*) as cnt FROM logs GROUP BY ip_address ORDER BY cnt DESC LIMIT 1"
    ).fetchone()

    code_frequencies = {}
    codes = db.execute("""SELECT status_code FROM logs""").fetchall()
    for code in codes:
        code = code['status_code']
        if code not in code_frequencies:
            code_frequencies[code] = 1
        else:
            code_frequencies[code] += 1

    timestamp_logs = {}
    timestamps = db.execute("""SELECT timestamp FROM logs ORDER BY timestamp DESC""").fetchall()
    for timestamp in timestamps:
        timestamp = timestamp['timestamp'][:-20]
        if timestamp not in timestamp_logs:
            timestamp_logs[timestamp] = 1
        else:
            timestamp_logs[timestamp] += 1

    error_hours = Counter()
    for entry in log_entries:
        code = int(entry['status_code'])
        if 400 <= code < 600:
            try:
                dt = datetime.datetime.strptime(entry['timestamp'][:20], "%d/%b/%Y:%H:%M:%S")
                hour = dt.hour
                error_hours[hour] += 1
            except Exception:
                continue

    error_hour_labels = [f"{h:02d}:00" for h in range(24)]
    error_hour_data = [error_hours.get(h, 0) for h in range(24)]

    unique_ip_groups = OrderedDict()
    for entry in log_entries:
        ip = entry['ip_address']
        key = '.'.join(ip.split('.')[:3]) 
        if key not in unique_ip_groups:
            unique_ip_groups[key] = ip

    unique_ips_location = {}
    for entry in log_entries:
        entry = entry['ip_address'].split(".")
        entry = '.'.join(entry[:2])
        if entry not in unique_ips_location:
            unique_ips_location[entry] = 1
        else:
            unique_ips_location[entry] += 1

    high_conc = []
    mid_conc = []
    low_conc = []
    for entry in log_entries:
        key = entry['ip_address'].split(".")
        key = '.'.join(key[:2])
        concentration = unique_ips_location[key]
        if concentration > 100:
            if key not in high_conc:
                high_conc.append(key)
        elif concentration > 50:
            if key not in mid_conc:
                mid_conc.append(key)
        else:
            if key not in low_conc:
                low_conc.append(key)

    unique_ips_count = len(unique_ip_groups)
    ips = list(unique_ip_groups.values())

    webscraper_entries = db.execute(
    "SELECT * FROM logs WHERE LOWER(user_agent) LIKE ? OR LOWER(user_agent) LIKE ? OR LOWER(user_agent) LIKE ?",
    ('%chatbot%', '%bot%', '%spider%')
    ).fetchall()

    high_conc_display = []
    mid_conc_display = []
    low_conc_display = []

    for ip in ips:
        for high in high_conc:
            if high in ip:
                high_conc_display.append(ip)
        for mid in mid_conc:
            if mid in ip:
                mid_conc_display.append(ip)
        for low in low_conc:
            if low in ip:
                low_conc_display.append(ip)

    return render_template(
        'index.html',
        form=form,
        log_entries=log_entries,
        ips=ips,
        total_requests=total_requests,
        avg_bytes=avg_bytes,
        most_common_status=most_common_status[0] if most_common_status else "N/A",
        most_common_ip=most_common_ip[0] if most_common_ip else "N/A",
        code_frequencies=code_frequencies,
        timestamp_logs=timestamp_logs,
        unique_ips_count=unique_ips_count,
        unique_ips_location=unique_ips_location,
        error_hour_labels=error_hour_labels,
        error_hour_data=error_hour_data,
        high_conc=high_conc,
        mid_conc=mid_conc,
        low_conc=low_conc,
        high_conc_display=high_conc_display,
        mid_conc_display=mid_conc_display,
        low_conc_display=low_conc_display,
        webscraper_entries=webscraper_entries
    )