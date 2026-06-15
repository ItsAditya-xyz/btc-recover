#!/usr/bin/env python3
"""
Generate candidates: pera/billetera + separator + [every Spanish word] (and reversed).

Based on CONFIRMED breach patterns only:
  pera6luz, pera5limon, Pera@chocolate5, pera%lus, pera5luz*

Separators: CONFIRMED only (5,6,7,8,@,%) + blank (direct concat)
Suffixes: CONFIRMED only (nothing, *)

Modes:
  python3 gen_spanish_combo.py pera        -> ~3-4M candidates
  python3 gen_spanish_combo.py billetera   -> ~3-4M candidates
  python3 gen_spanish_combo.py all         -> both

Run on VPS after targeted_wordlist.txt finishes:

  # Step 1 - pera + Spanish (uses same tried file to skip already-tested)
  python3 gen_spanish_combo.py pera > pera_spanish.txt 2>pera_spanish.log
  python3 recover.py --wordlist-only --wordlist pera_spanish.txt \\
    --tried tried_targeted.txt --meta meta_pera_es.json --procs 1

  # Step 2 - billetera + Spanish (also skips everything already tried)
  python3 gen_spanish_combo.py billetera > bill_spanish.txt 2>bill_spanish.log
  python3 recover.py --wordlist-only --wordlist bill_spanish.txt \\
    --tried tried_targeted.txt --meta meta_bill_es.json --procs 1
"""
import sys
import io

SPANISH_DICT = 'wordlists/spanish.txt'

# Confirmed separators ONLY (from real breach passwords)
SEPS = [
    '',            # peraluz (direct concat)
    '5', '6', '7', '8',   # pera6luz, pera5limon, pera5luz*
    '@', '%',              # Pera@chocolate5, pera%lus
]

# Confirmed suffixes only
SUFFIXES = ['', '*']

def load_spanish():
    words = []
    with open(SPANISH_DICT, encoding='utf-8', errors='ignore') as f:
        for line in f:
            w = line.strip()
            if w and 2 <= len(w) <= 14:
                words.append(w)
    return words

def run(anchor_word, spanish_words, out):
    seen = set()
    count = 0

    # anchor forms: lower + capitalize (pera/Pera, billetera/Billetera)
    anchor_forms = [anchor_word.lower(), anchor_word.capitalize()]

    for sp_word in spanish_words:
        # spanish word forms: lower + capitalize only
        sp_forms = [sp_word.lower(), sp_word.capitalize()]

        for af in anchor_forms:
            for sf in sp_forms:
                for sep in SEPS:
                    for suf in SUFFIXES:
                        # anchor + sep + spanish + suffix  (e.g. pera5billete*)
                        c = af + sep + sf + suf
                        if c not in seen and 5 <= len(c) <= 22:
                            seen.add(c)
                            out.write(c + '\n')
                            count += 1

                        # reversed: spanish + sep + anchor + suffix
                        # (pera is always first in breach, but billetera may come after)
                        c2 = sf + sep + af + suf
                        if c2 not in seen and 5 <= len(c2) <= 22:
                            seen.add(c2)
                            out.write(c2 + '\n')
                            count += 1

    sys.stderr.write(f'[{anchor_word}] {count:,} candidates written\n')
    return count

def main():
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else 'all'
    if mode not in ('pera', 'billetera', 'all'):
        print(f'Usage: {sys.argv[0]} [pera|billetera|all]', file=sys.stderr)
        sys.exit(1)

    spanish = load_spanish()
    sys.stderr.write(f'Loaded {len(spanish)} Spanish words\n')

    out = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    total = 0

    if mode in ('pera', 'all'):
        total += run('pera', spanish, out)
    if mode in ('billetera', 'all'):
        total += run('billetera', spanish, out)

    out.flush()
    sys.stderr.write(f'Total: {total:,} candidates\n')

if __name__ == '__main__':
    main()
