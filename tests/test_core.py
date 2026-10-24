"""
Full core verification for SlothDesk.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("[1/4] Importing main app...", flush=True)
from main import (
    app,
    janitor_service,
    CHAOTIC_SANDBOX_FILES,
    health_check,
    get_drawers,
    get_sandbox_default,
    messify_sandbox,
)
print(f"      App imported: {app.title}", flush=True)

print("[2/4] Testing classification on CHAOTIC_SANDBOX_FILES...", flush=True)
plan = janitor_service.plan_sandbox_organization(CHAOTIC_SANDBOX_FILES)
assert plan.total_files == len(CHAOTIC_SANDBOX_FILES), "File count mismatch"
assert plan.metrics.laziness_score > 50, "Laziness score should be > 50"
print(f"      Organized {plan.total_files} files. Laziness score: {plan.metrics.laziness_score}%", flush=True)

print("[3/4] Testing smart drawer assignments...", flush=True)
for drawer_name, items in plan.drawers.items():
    print(f"      Drawer '{drawer_name}': {len(items)} files", flush=True)
    for it in items:
        print(f"        -> {it.original_name} => {it.proposed_name} ({int(it.confidence*100)}%)", flush=True)

print("[4/4] Testing API endpoint logic...", flush=True)
h = health_check()
assert h["status"] == "ok"
print(f"      health_check() -> {h}", flush=True)

drawers = get_drawers()
assert len(drawers) == 5
print(f"      get_drawers() -> {len(drawers)} drawers", flush=True)

defaults = get_sandbox_default()
assert len(defaults) == 10
print(f"      get_sandbox_default() -> {len(defaults)} files", flush=True)

scrambled = messify_sandbox()
assert len(scrambled) == 10
print(f"      messify_sandbox() -> {len(scrambled)} files", flush=True)

print("\n[SUCCESS] CLASSIFIER, JANITOR & API VERIFIED SUCCESSFULLY!", flush=True)
