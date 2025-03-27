import json
import sys
import collections

def main():
    with open(sys.argv[1], "r") as f:
        gold = json.load(f)
    with open(sys.argv[2], "r") as f:
        gate = json.load(f)
    
    # Count events by type in both files
    gold_counts = collections.Counter()
    gate_counts = collections.Counter()
    
    # For each peripheral+event+payload combination, count occurrences
    for ev in gold["events"]:
        key = (ev["peripheral"], ev["event"], str(ev["payload"]))
        gold_counts[key] += 1
    
    for ev in gate["events"]:
        key = (ev["peripheral"], ev["event"], str(ev["payload"]))
        gate_counts[key] += 1
    
    # Now compare the counts
    all_keys = set(gold_counts.keys()) | set(gate_counts.keys())
    
    mismatches = 0
    for key in sorted(all_keys):
        gold_count = gold_counts[key]
        gate_count = gate_counts[key]
        
        if gold_count != gate_count:
            print(f"Count mismatch for {key}:")
            print(f"  Reference count: {gold_count}")
            print(f"  Test count:      {gate_count}")
            mismatches += 1
    
    if mismatches > 0:
        print(f"Found {mismatches} count mismatches between reference and test output")
        sys.exit(1)
    else:
        print("Event counts are identical (ignoring timestamps and order)")
        return 0

if __name__ == "__main__":
    main()
