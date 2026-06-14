#!/usr/bin/env bash
# Phase 2: Wordlist-only runs
# Safe to stop and restart at any time:
#   - Completed phases are skipped (done/<phase>.done marker files)
#   - Mid-phase runs resume via their --tried log (no repeats)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HASH="$SCRIPT_DIR/hash.txt"
WL="$SCRIPT_DIR/wordlists"
DONE="$WL/done"
mkdir -p "$DONE"

check_found() {
    if [[ -f "$SCRIPT_DIR/FOUND.txt" ]]; then
        echo ""
        echo "[!!!] FOUND.txt exists - password cracked! Stopping."
        cat "$SCRIPT_DIR/FOUND.txt"
        exit 0
    fi
}

run_phase() {
    local label="$1"
    local marker="$2"
    local wordlist="$3"
    local tried="$4"
    local meta="$5"

    if [[ -f "$DONE/$marker.done" ]]; then
        echo ""
        echo "=== $label - already completed, skipping ==="
        return
    fi

    echo ""
    echo "=== $label ==="
    python3 "$SCRIPT_DIR/recover.py" \
        --hash "$HASH" \
        --wordlist-only --wordlist "$wordlist" \
        --tried "$tried" --meta "$meta"

    check_found
    touch "$DONE/$marker.done"
    echo "  [marked complete: $marker]"
}

run_phase "Phase 2a: Spanish dictionary (71k words)  ~16 min" \
    "spanish" "$WL/spanish.txt" "$WL/tried_spanish.txt" "$WL/meta_spanish.json"

run_phase "Phase 2b: rockyou top 75% (59k passwords)  ~13 min" \
    "rk75" "$WL/rockyou_top75pct.txt" "$WL/tried_rk75.txt" "$WL/meta_rk75.json"

run_phase "Phase 2c: 10k most common passwords  ~3 min" \
    "10k" "$WL/common_10k.txt" "$WL/tried_10k.txt" "$WL/meta_10k.json"

run_phase "Phase 2d: Full rockyou part 1 (7.1M passwords)  ~27 hrs" \
    "rockyou_p1" "$WL/rockyou_part1.txt" "$WL/tried_rockyou.txt" "$WL/meta_rockyou_p1.json"

run_phase "Phase 2e: Full rockyou part 2 (7.1M passwords)  ~27 hrs" \
    "rockyou_p2" "$WL/rockyou_part2.txt" "$WL/tried_rockyou.txt" "$WL/meta_rockyou_p2.json"

echo ""
echo "All Phase 2 wordlists exhausted. No match."
echo "Next: cloud GPU + hashcat -m 11300, or btcrecover with a tokenlist."
