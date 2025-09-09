#!/usr/bin/env python3
"""Run a single /health probe against localhost:8000 and print the
status.

This is intended to be executed inside the api container. For example:
`docker exec <container> python /app/scripts/wait_for_health_container.py`.

The script prints the numeric status (e.g. 200) or 'err' on failure and
exits 0 on success.
"""
import http.client
import sys

try:
    conn = http.client.HTTPConnection("localhost", 8000, timeout=5)
    conn.request("GET", "/health")
    r = conn.getresponse()
    print(r.status)
    sys.exit(0 if r.status == 200 else 1)
except Exception:
    print("err")
    sys.exit(1)
