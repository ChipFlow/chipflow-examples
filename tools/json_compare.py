import json
import os
import sys
from pathlib import Path
from pprint import pformat

working_dir = Path(os.environ["PDM_RUN_CWD"] if "PDM_RUN_CWD" in os.environ else "./")

gold_path = Path(sys.argv[1])
gate_path = Path(sys.argv[2])

gold_path = gold_path if gold_path.is_absolute() else working_dir / gold_path
gate_path = gate_path if gate_path.is_absolute() else working_dir / gate_path

def on_ci():
    if "CI" in os.environ and os.environ["CI"]:
        return True
    return False

def main():
    with open(gold_path, "r") as f:
        gold = json.load(f)
    with open(gate_path, "r") as f:
        gate = json.load(f)
    if len(gold["events"]) != len(gate["events"]):
        print(f"Failed! Event mismatch: {len(gold['events'])} events in reference, {len(gate['events'])} in test output")
        if on_ci():
            print(f"Test Output:\n{pformat(gate)}\n")
            print(f"Reference events:\n{pformat(gold)}\n")
        return 1
    for ev_gold, ev_gate in zip(gold["events"], gate["events"]):
        if ev_gold["peripheral"] != ev_gate["peripheral"] or \
           ev_gold["event"] != ev_gate["event"] or \
           ev_gold["payload"] != ev_gate["payload"]:
            print(f"Failed! Reference event {ev_gold} mismatches test event {ev_gate}")
            return 1

    print("Success! Event logs are identical")
    return 0

if __name__ == "__main__":
    main()
