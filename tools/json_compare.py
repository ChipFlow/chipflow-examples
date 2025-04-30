import json
import os
import sys
from pathlib import Path

working_dir = Path(os.environ["PDM_RUN_CWD"] if "PDM_RUN_CWD" in os.environ else "./")

gold_path = Path(sys.argv[1])
gate_path = Path(sys.argv[2])

gold_path = gold_path if gold_path.is_absolute() else working_dir / gold_path
gate_path = gate_path if gate_path.is_absolute() else working_dir / gate_path

def main():
    with open(gold_path, "r") as f:
        gold = json.load(f)
    with open(gate_path, "r") as f:
        gate = json.load(f)
    assert len(gold["events"]) == len(gate["events"]), f"mismatch: {len(gold['events'])} events in reference, {len(gate['events'])} in test output"
    for ev_gold, ev_gate in zip(gold["events"], gate["events"]):
        for field in ("peripheral", "event", "payload"):
            assert ev_gold["peripheral"] == ev_gate["peripheral"] and ev_gold["event"] == ev_gate["event"] and ev_gold["payload"] == ev_gate["payload"], \
                f"reference event {ev_gold} mismatches test event {ev_gate} beyond timestamp"
    print("Event logs are identical")


if __name__ == "__main__":
    main()
