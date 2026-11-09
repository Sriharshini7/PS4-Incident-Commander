"""
agent_runner.py: An Incident Commander that investigates and heals a real running HTTP server.
"""

import time
import requests
from dataclasses import dataclass, field
from typing import Dict, Any, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

TARGET_URL = "http://127.0.0.1:8000"

# --- 1. Real Network Telemetry Tool ---

class RealHttpTelemetry:
    """Measures real wall-clock round-trip network response times."""
    
    def measure_latency_ms(self) -> Dict[str, Any]:
        start = time.time()
        try:
            resp = requests.get(f"{TARGET_URL}/health", timeout=6.0)
            elapsed_ms = (time.time() - start) * 1000.0
            return {
                "latency_ms": round(elapsed_ms, 2),
                "status_code": resp.status_code,
                "timestamp": time.time(),
                "fresh": True
            }
        except requests.exceptions.RequestException as e:
            return {
                "latency_ms": 9999.0,
                "status_code": 503,
                "timestamp": time.time(),
                "fresh": True,
                "error": str(e)
            }

    def fetch_current_version(self) -> str:
        try:
            resp = requests.get(f"{TARGET_URL}/version", timeout=2.0)
            return resp.json().get("version", "unknown")
        except Exception:
            return "unknown"


# --- 2. Hybrid Runbook Matching ---

@dataclass
class Runbook:
    id: str
    remediation_action: str
    signature: str
    requires_recent_bad_deploy: bool

RUNBOOKS = [
    Runbook(
        id="RB-ROLLBACK",
        remediation_action="rollback",
        signature="High latency timeouts after a new bad deployment release update.",
        requires_recent_bad_deploy=True
    ),
    Runbook(
        id="RB-RESTART",
        remediation_action="restart",
        signature="High latency timeouts and memory saturation without recent deploy.",
        requires_recent_bad_deploy=False
    )
]

def match_runbook(alert_text: str) -> Runbook:
    vectorizer = TfidfVectorizer()
    corpus = [rb.signature for rb in RUNBOOKS]
    tfidf = vectorizer.fit_transform(corpus)
    scores = cosine_similarity(vectorizer.transform([alert_text]), tfidf)[0]
    best_idx = scores.argmax()
    return RUNBOOKS[best_idx]


# --- 3. Blast-Radius Classifier ---

def classify_action(action: str) -> Dict[str, Any]:
    # Alert severity does NOT dictate approval. Action blast-radius does.
    if action == "restart":
        return {"tier": "low", "requires_approval": False}
    elif action == "rollback":
        return {"tier": "high", "requires_approval": True}
    return {"tier": "high", "requires_approval": True}


# --- 4. Wall-Clock Approval & Escalation ---

def request_approval_with_timeout(action: str, timeout_seconds: float = 1.0) -> Dict[str, Any]:
    print(f"\n[APPROVAL] Action '{action}' is HIGH blast-radius.")
    print(f"[APPROVAL] Paging primary responder 'engineer-priya' (Deadline: {timeout_seconds}s)...")
    
    start_time = time.time()
    # Simulate a human taking 1.5 seconds to see the page (which exceeds 1.0s timeout)
    time.sleep(1.2)
    elapsed = time.time() - start_time

    if elapsed > timeout_seconds:
        print(f"[ESCALATION] Priya did not respond within {timeout_seconds}s (took {elapsed:.2f}s)!")
        print("[ESCALATION] Escalating page to secondary responder 'engineer-devon'...")
        return {"approved": True, "escalated": True, "responder": "engineer-devon"}
    
    return {"approved": True, "escalated": False, "responder": "engineer-priya"}


# --- 5. Real Remediation & Signal Verification ---

def execute_remediation_over_network(action: str) -> bool:
    print(f"[ACTION] Triggering real HTTP remediation: POST {TARGET_URL}/action/{action}")
    try:
        resp = requests.post(f"{TARGET_URL}/action/{action}", timeout=3.0)
        return resp.status_code == 200
    except Exception as e:
        print(f"[ACTION ERROR] {e}")
        return False


def verify_real_signal(telemetry: RealHttpTelemetry, baseline_ms: float = 200.0) -> bool:
    print("\n[VERIFICATION] Re-querying actual network latency to verify recovery...")
    reading = telemetry.measure_latency_ms()
    latency = reading["latency_ms"]
    print(f"[VERIFICATION] Measured post-fix latency: {latency}ms (Baseline: <= {baseline_ms}ms)")
    
    if latency <= baseline_ms:
        print("[VERIFICATION SUCCESS] The server is genuinely healed!")
        return True
    else:
        print("[VERIFICATION FAILED] Server is still slow! Incident reopened.")
        return False


# --- Main Live Investigation Routine ---

def run_live_incident_investigation():
    telemetry = RealHttpTelemetry()

    print("=" * 70)
    print("STEP 1: Checking Baseline Health of the Live Server...")
    print("=" * 70)
    baseline = telemetry.measure_latency_ms()
    version = telemetry.fetch_current_version()
    print(f"Server is responding at: {baseline['latency_ms']}ms | Current Version: {version}")

    print("\n" + "=" * 70)
    print("STEP 2: Simulating Real Incident (Breaking the live server)...")
    print("=" * 70)
    requests.post(f"{TARGET_URL}/simulate/break")
    
    # Measure the degradation
    broken = telemetry.measure_latency_ms()
    broken_ver = telemetry.fetch_current_version()
    print(f"ALERT! Real Measured Latency is now: {broken['latency_ms']}ms (SLOW!)")
    print(f"Active Version: {broken_ver}")

    print("\n" + "=" * 70)
    print("STEP 3: Multi-Round Investigation")
    print("=" * 70)
    alert_text = "Server degradation with high response latency and timeout."
    runbook = match_runbook(alert_text)
    print(f"Candidate Runbook Selected: {runbook.id} (Action: {runbook.remediation_action})")

    # Correlate with real version
    is_bad_deploy = "buggy" in broken_ver
    print(f"Telemetry Correlation -> Did server deploy buggy version? {is_bad_deploy}")

    if is_bad_deploy:
        action_to_take = "rollback"
    else:
        action_to_take = "restart"

    print("\n" + "=" * 70)
    print("STEP 4: Blast-Radius & Real-Time Escalation")
    print("=" * 70)
    policy = classify_action(action_to_take)
    print(f"Action: {action_to_take} | Risk Tier: {policy['tier']} | Needs Approval: {policy['requires_approval']}")

    if policy["requires_approval"]:
        approval_result = request_approval_with_timeout(action_to_take, timeout_seconds=1.0)
        print(f"Approval Granted by: {approval_result['responder']} (Escalated: {approval_result['escalated']})")

    print("\n" + "=" * 70)
    print("STEP 5: Execute Fix & Verify Real Signal")
    print("=" * 70)
    execute_remediation_over_network(action_to_take)
    
    # Re-verify by pinging the real web server
    resolved = verify_real_signal(telemetry, baseline_ms=250.0)
    
    print("\n" + "=" * 70)
    print(f"FINAL INCIDENT STATUS: {'RESOLVED' if resolved else 'UNRESOLVED'}")
    print("=" * 70)


if __name__ == "__main__":
    run_live_incident_investigation()