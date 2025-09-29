#!/usr/bin/env python3
"""Minimal container smoke test:

Checks:
 - GET /health -> {"status":"ok"}
 - One minimal product discovery flow (ask -> reply budget -> reply brand -> reply tech)

On any assertion failure the script exits non‑zero so CI can fail fast.
"""

import http.client
import json
import os
import sys
import time

# Detect if running inside container vs locally
if os.path.exists("/app") and os.environ.get("DOCKER_CONTAINER") != "false":
    # Running inside container - connect to API service via Docker network
    API_HOST = "api"
    API_PORT = 8000
    OUTPUT_FILE = "/app/pixie_test_output.json"
else:
    # Running locally - connect to localhost with mapped port
    API_HOST = "localhost"
    API_PORT = 8012
    OUTPUT_FILE = "pixie_test_output.json"


def get(path):
    conn = http.client.HTTPConnection(API_HOST, API_PORT)
    conn.request("GET", path)
    r = conn.getresponse()
    data = r.read().decode()
    conn.close()
    try:
        return r.status, json.loads(data)
    except Exception:
        return r.status, {"raw": data}


def post(body):
    conn = http.client.HTTPConnection(API_HOST, API_PORT)
    conn.request(
        "POST",
        "/ask",
        body=json.dumps(body),
        headers={"Content-Type": "application/json"},
    )
    r = conn.getresponse()
    data = r.read().decode()
    conn.close()
    try:
        return r.status, json.loads(data)
    except Exception:
        return r.status, {"raw": data}


out = {"health": None, "flow": []}

# Health check
status, body = get("/health")
out["health"] = {"status_code": status, "body": body}
if status != 200 or not isinstance(body, dict) or body.get("status") != "ok":
    print("Health check failed:", status, body)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(2)

# Give database seeding a moment to complete if needed
print("Waiting 3 seconds for database seeding to complete...")
time.sleep(3)

# Minimal product discovery smoke flow
status, r1 = post({"question": "Ik zoek een nieuwe printer"})
out["flow"].append({"step": 1, "status": status, "resp": r1})
if status != 200 or r1.get("type") != "ask_user":
    print("Step 1 failed:", status, r1)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(3)

pending = r1.get("pending_id")
if not pending:
    print("No pending_id returned in step 1")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(4)

# Reply budget -> expect ask_user
status, r2 = post({"pending_id": pending, "message": "Maximaal 200€"})
out["flow"].append({"step": 2, "status": status, "resp": r2})
if status != 200 or r2.get("type") != "ask_user":
    print("Step 2 failed:", status, r2)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(5)

pending = r2.get("pending_id") or pending

# Reply brand -> expect ask_user
status, r3 = post({"pending_id": pending, "message": "Brother"})
out["flow"].append({"step": 3, "status": status, "resp": r3})
if status != 200 or r3.get("type") != "ask_user":
    print("Step 3 failed:", status, r3)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(6)

pending = r3.get("pending_id") or pending

# Reply tech -> expect answer
status, r4 = post({"pending_id": pending, "message": "laser"})
out["flow"].append({"step": 4, "status": status, "resp": r4})
if status != 200 or r4.get("type") != "answer":
    print(f"Step 4 failed: Expected answer with products, got: {status} {r4}")
    print("This typically means no products matched the search criteria.")
    print("Check database seeding and search engine configuration.")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(7)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(json.dumps(out, ensure_ascii=False, indent=2))

print(f"Smoke test succeeded; wrote {OUTPUT_FILE}")
sys.exit(0)
