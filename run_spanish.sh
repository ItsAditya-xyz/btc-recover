#!/usr/bin/env bash
# Run AFTER targeted_wordlist.txt phase completes.
# Generates pera/billetera + every Spanish word (7M+ candidates each).
# Uses tried_targeted.txt as master skip-file — never re-tests anything already tried.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HASH="$SCRIPT_DIR/hash.txt"
TRIED="$SCRIPT_DIR/tried_targeted.txt"   # master skip file (shared across all phases)

check_found() {
    if [[ -f "$SCRIPT_DIR/FOUND.txt" ]]; then
        echo ""
        echo "[!!!] PASSWORD FOUND — check FOUND.txt"
        cat "$SCRIPT_DIR/FOUND.txt"
        exit 0
    fi
}

echo "=== Phase A: pera + every Spanish word (~7M candidates, ~18h) ==="
python3 "$SCRIPT_DIR/gen_spanish_combo.py" pera > "$SCRIPT_DIR/pera_spanish.txt" 2>"$SCRIPT_DIR/pera_spanish.log"
cat "$SCRIPT_DIR/pera_spanish.log"
python3 "$SCRIPT_DIR/recover.py" \
    --hash "$HASH" \
    --wordlist-only \
    --wordlist "$SCRIPT_DIR/pera_spanish.txt" \
    --tried "$TRIED" \
    --meta "$SCRIPT_DIR/meta_pera_es.json" \
    --procs 1
check_found

echo ""
echo "=== Phase B: billetera + every Spanish word (~7M candidates, ~18h) ==="
python3 "$SCRIPT_DIR/gen_spanish_combo.py" billetera > "$SCRIPT_DIR/bill_spanish.txt" 2>"$SCRIPT_DIR/bill_spanish.log"
cat "$SCRIPT_DIR/bill_spanish.log"
python3 "$SCRIPT_DIR/recover.py" \
    --hash "$HASH" \
    --wordlist-only \
    --wordlist "$SCRIPT_DIR/bill_spanish.txt" \
    --tried "$TRIED" \
    --meta "$SCRIPT_DIR/meta_bill_es.json" \
    --procs 1
check_found

echo ""
echo "All Spanish combo phases exhausted. No match."
