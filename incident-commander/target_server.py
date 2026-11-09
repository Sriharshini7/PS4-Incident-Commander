"""
target_server.py: A real microservice with health checks, configurable lag, and crash modes.
Run with: uvicorn target_server:app --port 8000
"""

import time
from fastapi import FastAPI, Response

app = FastAPI()

# Server state
state = {
    "version": "v1.0.0",
    "is_degraded": False,
    "lag_seconds": 0.0,
    "restart_count": 0
}

@app.get("/")
def root():
    return {"status": "ok", "version": state["version"]}

@app.get("/health")
def health():
    # If the server is in degraded mode, inject real response latency
    if state["is_degraded"]:
        time.sleep(state["lag_seconds"])
        return Response(
            content='{"status": "degraded", "detail": "high latency under memory pressure"}',
            media_type="application/json",
            status_code=200
        )
    return {"status": "healthy", "version": state["version"], "restarts": state["restart_count"]}

@app.get("/version")
def get_version():
    return {"version": state["version"]}

# --- Control Endpoints (used to trigger issues or remediate) ---

@app.post("/simulate/break")
def break_server():
    """Simulates a bad deployment: introduces a 3.5s latency lag."""
    state["is_degraded"] = True
    state["lag_seconds"] = 3.5
    state["version"] = "v2.0.0-buggy"
    return {"message": "Server degraded. Latency set to 3.5s, version set to v2.0.0-buggy."}

@app.post("/action/rollback")
def rollback_server():
    """Remediation: rolls back the release and restores normal speed."""
    state["is_degraded"] = False
    state["lag_seconds"] = 0.0
    state["version"] = "v1.0.0"
    return {"message": "Rollback successful. Version reset to v1.0.0, normal latency restored."}

@app.post("/action/restart")
def restart_server():
    """Remediation: clears transient memory leak."""
    state["is_degraded"] = False
    state["lag_seconds"] = 0.0
    state["restart_count"] += 1
    return {"message": "Service restarted. Latency restored to baseline."}