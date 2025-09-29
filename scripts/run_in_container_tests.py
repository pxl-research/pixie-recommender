#!/usr/bin/env python3
"""Minimal container smoke test:

Checks:
 - GET /health -> {"status":"ok"}
 - One minimal product discovery flow (ask -> reply budget -> reply brand -> reply tech)

On any assertion failure the script exits non‑zero so CI can fail fast.
"""

import http.client as http_client
import json
import os
import socket
import sys
import time


# Determine API host/port. Allow explicit overrides via env vars for CI flexibility.
def _probe(host: str, port: int, timeout: float = 0.8) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


OUTPUT_FILE = "pixie_test_output.json"

# Default API endpoint values (typed) so static checkers don't see None
API_HOST: str = "localhost"
API_PORT: int = 8012

# Respect explicit environment overrides first
env_host = os.environ.get("API_HOST")
env_port = os.environ.get("API_PORT")
env_url = os.environ.get("API_URL")
if env_url and ":" in env_url:
    try:
        h, p = env_url.split(":")
        API_HOST = h
        API_PORT = int(p)
    except Exception:
        API_HOST = env_host or "localhost"
        API_PORT = int(env_port) if env_port else 8012
elif env_host or env_port:
    API_HOST = env_host or "localhost"
    API_PORT = int(env_port) if env_port else 8012
else:
    # No explicit override: build a candidate list depending on runtime
    OUTPUT_FILE = (
        "/app/pixie_test_output.json"
        if os.path.exists("/app")
        else "pixie_test_output.json"
    )

    # Prefer the host/port mapping that matches a typical container-first setup,
    # but probe a short list and pick the first reachable endpoint.
    candidates = []
    if os.path.exists("/app"):
        # We're inside a container (could be the api container or a helper container).
        candidates = [("localhost", 8000), ("api", 8000), ("localhost", 8012)]
    else:
        # Running on host; try host-mapped port first then internal service name.
        candidates = [("localhost", 8012), ("api", 8000), ("localhost", 8000)]

    found = False
    for h, p in candidates:
        if _probe(h, p):
            API_HOST = h
            API_PORT = p
            found = True
            break

    # Fall back to sensible defaults if none probe succeeded
    if not found:
        if os.path.exists("/app"):
            API_HOST, API_PORT = "api", 8000
        else:
            API_HOST, API_PORT = "localhost", 8012

    # OUTPUT_FILE already set above for host/container (kept earlier as default)

# If an explicit OUTPUT_PATH env var is provided, use it
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", OUTPUT_FILE)

# Ensure types are correct for http client
API_HOST = str(API_HOST)
API_PORT = int(API_PORT)

# Print chosen endpoint for debugging in CI logs (split to keep lines short)
print("Using API endpoint:", f"{API_HOST}:{API_PORT}")
print(f"Overrides: API_HOST={env_host}, API_PORT={env_port}, API_URL={env_url}")


def get(path):
    conn = http_client.HTTPConnection(API_HOST, API_PORT)
    conn.request("GET", path)
    r = conn.getresponse()
    data = r.read().decode()
    conn.close()
    try:
        return r.status, json.loads(data)
    except Exception:
        return r.status, {"raw": data}


def post(body):
    conn = http_client.HTTPConnection(API_HOST, API_PORT)
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


def post_to_endpoint(endpoint, body):
    """POST to arbitrary endpoint."""
    conn = http_client.HTTPConnection(API_HOST, API_PORT)
    conn.request(
        "POST",
        endpoint,
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

# Verify database has data before starting the flow
print("Verifying database seeding completed...")
max_retries = 5
retry_count = 0

while retry_count < max_retries:
    try:
        # Check database status via debug endpoint
        db_status, db_resp = get("/debug/db-status")

        if db_status == 200 and isinstance(db_resp, dict):
            if db_resp.get("seeding_complete"):
                print(
                    f"✅ Database verification passed - "
                    f"found {db_resp.get('product_count', 0)} products"
                )
                break
            else:
                print(
                    f"⚠️  Database not ready: products={db_resp.get('product_count', 0)}, "
                    f"attr_def={db_resp.get('attribute_definition_count', 0)}, "
                    f"attr_val={db_resp.get('product_attribute_value_count', 0)} "
                    f"(attempt {retry_count + 1}/{max_retries})"
                )
        else:
            print(
                f"⚠️  Debug endpoint error: {db_status} {db_resp} "
                f"(attempt {retry_count + 1}/{max_retries})"
            )

    except Exception as e:
        print(
            f"⚠️  Exception during verification: {e} (attempt {retry_count + 1}/{max_retries})"
        )

    retry_count += 1
    if retry_count < max_retries:
        print("   Waiting 2 more seconds and retrying...")
        time.sleep(2)

if retry_count >= max_retries:
    print("❌ Database verification failed after all retries")
    print("   Attempting to reset database configuration and force seeding...")

    # Try to reset the database configuration in case of cached connection issues
    try:
        reset_status, reset_resp = post_to_endpoint("/debug/reset-db-connection", {})
        if reset_status == 200 and isinstance(reset_resp, dict):
            new_url = reset_resp.get("new_database_url", "unknown")
            print(f"✅ Configuration reset successful: {new_url}")
        else:
            print(f"⚠️  Configuration reset failed: {reset_status} {reset_resp}")
    except Exception as e:
        print(f"⚠️  Could not reset configuration: {e}")

    # Try to trigger seeding by calling the API health endpoint multiple times
    for i in range(3):
        try:
            get("/health")
            time.sleep(1)
        except Exception:
            pass

    # One final check
    try:
        db_status, db_resp = get("/debug/db-status")
        if db_status == 200 and db_resp.get("seeding_complete"):
            print(
                f"✅ Forced seeding succeeded - found {db_resp.get('product_count', 0)} products"
            )
        else:
            print("❌ Forced seeding failed - this will likely cause test failure")
            print(f"   Final DB state: {db_resp}")
    except Exception:
        print("❌ Could not check final database state")
else:
    print("   Database verification completed successfully")

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

    # Enhanced debugging for CI
    print("\n=== DEBUG INFORMATION ===")
    try:
        db_status, db_resp = get("/debug/db-status")
        print(f"Database status: {db_status} {db_resp}")
    except Exception as e:
        print(f"Could not get database status: {e}")

    print("Conversation flow so far:")
    for i, step in enumerate(out["flow"], 1):
        resp_type = step["resp"].get("type", "unknown")
        pending_id = step["resp"].get("pending_id", "none")
        prompt = (
            step["resp"].get("prompt", "")[:50] + "..."
            if step["resp"].get("prompt")
            else ""
        )
        print(f"  Step {i}: {resp_type}, pending_id={pending_id}, prompt='{prompt}'")

    print("=========================")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(7)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(json.dumps(out, ensure_ascii=False, indent=2))

print(f"Smoke test succeeded; wrote {OUTPUT_FILE}")
sys.exit(0)
