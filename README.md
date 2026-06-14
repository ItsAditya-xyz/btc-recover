# Bitcoin Wallet Password Recovery

Self-recovery tool for an encrypted Bitcoin Core `wallet.dat` from 2013.

## Files

| File | Purpose |
|------|---------|
| `recover.py` | Main cracker — generates candidates, runs parallel KDF checks |
| `hash.txt` | The `$bitcoin$` hash extracted from `wallet.dat` |
| `base_words.txt` | Seed words (Spanish/English wallet terms, name, dates) |
| `tried.txt` | Every failed candidate from the targeted run (auto-resume) |
| `tried_big.txt` | Every failed candidate from the big-masks run (auto-resume) |
| `tried_meta.json` | JSON status of the targeted run |
| `tried_big_meta.json` | JSON status of the big-masks run |
| `run.log` | Terminal output from the targeted run |
| `run_big.log` | Terminal output from the big-masks run |
| `FOUND.txt` | Written only if password is found — contains the password |

## Requirements

```
Python 3.x
pycryptodome    (pip install pycryptodome)
```

## Running

### Verify the engine is correct
```
python recover.py --selftest
```

### Run 1 — Targeted (word variants + combinator + light masks)
Covers ~150k high-probability candidates built from `base_words.txt`.
```
python recover.py --hash hash.txt --words base_words.txt --tried tried.txt --meta tried_meta.json
```

### Run 2 — Big masks (word + 0–99,999)
Covers ~960k candidates: every base word paired with every 5-digit number.
```
python recover.py --hash hash.txt --words base_words.txt --big --tried tried_big.txt --meta tried_big_meta.json
```

### Run 3 — External wordlist (e.g. rockyou, Spanish lists)
Skip candidate generation; test a downloaded wordlist directly.
```
python recover.py --hash hash.txt --wordlist-only --wordlist rockyou.txt --tried tried_wl.txt --meta tried_wl_meta.json
```

### Combine a wordlist with generated candidates
```
python recover.py --hash hash.txt --words base_words.txt --wordlist spanish.txt --tried tried.txt --meta tried_meta.json
```

## Resume after interruption

Runs are automatically resumed — already-tested candidates are skipped.
Just re-run the exact same command; the `--tried` file is read on startup:
```
[+] resume: 45,000 words already tried -> skipping 45,000
[+] 107,864 unique candidates to try
```

To force a full restart from scratch:
```
python recover.py ... --no-resume
```

## Checking status

```powershell
# Latest progress line
Get-Content run.log -Tail 3

# JSON status
Get-Content tried_meta.json

# How many candidates have been tried
(Get-Content tried.txt | Measure-Object -Line).Lines

# Check if password was found
Get-Content FOUND.txt
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--hash` | `hash.txt` | Hash string or path to hash file |
| `--words` | `base_words.txt` | Seed words for candidate generation |
| `--wordlist` | — | Extra plain wordlist to append |
| `--wordlist-only` | off | Skip generated candidates; use only `--wordlist` |
| `--big` | off | Extend numeric masks to 0–99,999 (~960k candidates) |
| `--tried` | `tried.txt` | File to log failed candidates (for resume) |
| `--meta` | `tried_meta.json` | JSON run summary |
| `--no-resume` | off | Ignore `--tried` file and start from scratch |
| `--procs` | all cores | Number of parallel worker processes |
| `--selftest` | off | Run built-in correctness test and exit |

## Recommended run strategy

### Step 1 — `--big` (most targeted, ~5 hrs)

Run this first. It uses everything known about the wallet owner — name, dates, Spanish money words, Bitcoin terms — and generates ~1M high-probability candidates. It is a strict superset of the plain targeted run, so there is no need to run both.

```powershell
python recover.py --hash hash.txt --words base_words.txt --big --tried tried_big.txt --meta tried_big_meta.json
```

Safe to stop and restart — already-tried words are skipped automatically via `tried_big.txt`.

### Step 2 — Phase 2 wordlists (if Step 1 misses)

Run this immediately after Step 1 finishes without a match. It runs four wordlists in order of relevance, stops the moment the password is found, and skips any phase that already completed on a previous run.

```powershell
.\run_phase2.ps1
```

| Phase | Wordlist | Candidates | Est. time |
|-------|----------|-----------|-----------|
| 2a | `spanish.txt` — 71k real Spanish words | 71,181 | ~16 min |
| 2b | `rockyou_top75pct.txt` — top 75% most common | 59,184 | ~13 min |
| 2c | `common_10k.txt` — universal top 10k | 10,000 | ~3 min |
| 2d/2e | `rockyou_part1/2.txt` — full 14M list | 14,344,391 | ~54 hrs |

> **Note:** Phases 2d/2e (full rockyou) take ~54 hrs on this machine. If Phases 2a–2c miss, consider a cloud GPU (RTX 3090 on Vast.ai ~$0.50/hr) running `hashcat -m 11300` instead — it completes the full rockyou in under an hour.

### Why this order

- **Step 1** is the highest-probability run — built entirely from personal context (name, birthday, location, Spanish vocabulary). If the password is something like `billetera2013`, `guille1969`, or `bitcoinpassword@2013`, it will be found here.
- **Phase 2a** (Spanish dictionary) is next most likely for a Spanish-speaking user who used a real word as a base.
- **Phases 2b–2c** (rockyou subsets) cast a wider net over real-world leaked passwords.
- **Phases 2d–2e** (full rockyou) are the last CPU-based resort before escalating to a GPU.

## How it works

Bitcoin Core encrypts the wallet master key with AES-256-CBC. The key/IV are derived from the passphrase + salt via iterated SHA-512:

```
buf = SHA512(passphrase + salt)
repeat (iters - 1) times: buf = SHA512(buf)
key = buf[0:32]
iv  = buf[32:48]
plaintext = AES-256-CBC-decrypt(key, iv, encrypted_master_key)
```

A correct password produces valid PKCS#7 padding (`\x10 * 16`) in the last block. This matches hashcat mode `-m 11300`.

The hash in this repo has **63,533 iterations** (low for a 2013 wallet), which makes CPU-based recovery feasible for a targeted attack.
