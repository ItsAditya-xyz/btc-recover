#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HASH="$SCRIPT_DIR/hash.txt"
WL="$SCRIPT_DIR/wordlists"
DONE="$WL/done"
mkdir -p "$DONE"

check_found() {
    if [[ -f "$SCRIPT_DIR/FOUND.txt" ]]; then
        echo ""
        echo "[!!!] PASSWORD FOUND:"
        cat "$SCRIPT_DIR/FOUND.txt"
        exit 0
    fi
}

run_phase() {
    local label="$1" marker="$2" extra_args="${3:-}"

    if [[ -f "$DONE/$marker.done" ]]; then
        echo "=== $label - already completed, skipping ==="
        return
    fi

    echo ""
    echo "=== $label ==="
    python3 "$SCRIPT_DIR/recover.py" --hash "$HASH" $extra_args
    check_found
    touch "$DONE/$marker.done"
}

# --- Step 1: targeted big run ---
run_phase "Step 1: targeted --big (~5 hrs)" "big" \
    "--words $SCRIPT_DIR/base_words.txt --big --tried $SCRIPT_DIR/tried_big.txt --meta $SCRIPT_DIR/tried_big_meta.json"

# --- Step 2: wordlist phases ---
run_phase "Step 2a: Spanish dictionary (71k words)" "spanish" \
    "--wordlist-only --wordlist $WL/spanish.txt --tried $WL/tried_spanish.txt --meta $WL/meta_spanish.json"

run_phase "Step 2b: rockyou top 75% (59k passwords)" "rk75" \
    "--wordlist-only --wordlist $WL/rockyou_top75pct.txt --tried $WL/tried_rk75.txt --meta $WL/meta_rk75.json"

run_phase "Step 2c: 10k most common passwords" "10k" \
    "--wordlist-only --wordlist $WL/common_10k.txt --tried $WL/tried_10k.txt --meta $WL/meta_10k.json"

run_phase "Step 2d: rockyou part 1 (7.1M passwords)" "rockyou_p1" \
    "--wordlist-only --wordlist $WL/rockyou_part1.txt --tried $WL/tried_rockyou.txt --meta $WL/meta_rockyou_p1.json"

run_phase "Step 2e: rockyou part 2 (7.1M passwords)" "rockyou_p2" \
    "--wordlist-only --wordlist $WL/rockyou_part2.txt --tried $WL/tried_rockyou.txt --meta $WL/meta_rockyou_p2.json"

echo ""
echo "All phases exhausted. No match found."
echo "Next: cloud GPU + hashcat -m 11300"
