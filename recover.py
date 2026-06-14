#!/usr/bin/env python3
"""
Bitcoin Core wallet password recovery (self-recovery).

Implements the exact Bitcoin Core KDF used by `wallet.dat`:
  buf = SHA512(passphrase || salt)
  repeat (iters-1) times: buf = SHA512(buf)
  key = buf[0:32], iv = buf[32:48]
Then AES-256-CBC-decrypts the encrypted master key and checks PKCS#7 padding
(the master key is 32 bytes, so the final block decrypts to 0x10 * 16).

This matches hashcat -m 11300 / bitcoin2john output:
  $bitcoin$<len>$<cry_master>$<saltlen>$<salt>$<iters>$2$00$2$00
"""
import sys, time, os, argparse, hashlib, itertools, json
from multiprocessing import Pool, cpu_count
from Crypto.Cipher import AES

PAD = b"\x10" * 16  # PKCS#7 padding for a 32-byte master key (48-byte ciphertext)

# ---------- hash parsing ----------
def parse_hash(text):
    p = text.strip().split("$")
    # ['', 'bitcoin', '96', '<cry>', '16', '<salt>', '63533', '2', '00', '2', '00']
    assert p[1] == "bitcoin", "not a $bitcoin$ hash"
    cry = bytes.fromhex(p[3])
    salt = bytes.fromhex(p[5])
    iters = int(p[6])
    return cry, salt, iters

# ---------- worker ----------
CRY = SALT = ITERS = None
def init_worker(cry, salt, iters):
    global CRY, SALT, ITERS
    CRY, SALT, ITERS = cry, salt, iters

def check(pw):
    buf = hashlib.sha512(pw.encode("utf-8", "ignore") + SALT).digest()
    for _ in range(ITERS - 1):
        buf = hashlib.sha512(buf).digest()
    pt = AES.new(buf[:32], AES.MODE_CBC, buf[32:48]).decrypt(CRY)
    return (pw, pt[-16:] == PAD)   # (candidate, matched?)

# ---------- candidate generation ----------
LEET = str.maketrans({"a":"4","e":"3","i":"1","o":"0","s":"5",
                      "A":"4","E":"3","I":"1","O":"0","S":"5"})
# z<->s swap: his own stated transformation ("cambio z por s o alreves")
Z2S = str.maketrans({"z":"s","Z":"S"})
S2Z = str.maketrans({"s":"z","S":"Z"})

def word_forms(w):
    forms = {w, w.lower(), w.upper(), w.capitalize(), w.title(), w.swapcase()}
    # z<->s swap: his stated transformation ("cambio z por s o alreves")
    for f in list(forms):
        forms.add(f.translate(Z2S))
        forms.add(f.translate(S2Z))
    for f in list(forms):
        forms.add(f.translate(LEET))
    return forms

SUFFIXES = ["", "1","2","3","12","123","1234","12345","01","00","11",
            "21","69","13","2013","1969","211169","21111969","2111","1121",
            "2008","2009","2010","2011","2012","2014","2015","2016",
            "5","6","7","8","56","67","78","567","678","5678",   # from survey
            "231661","23166","2316",                              # from survey
            "!","!!","?",".","#","$","*","123!","2013!","1969!","21!",
            "_","-","2013.","69!","00!"]
PREFIXES = ["", "!", "1", "0", "#"]
SEPS = ["", " ", ".", "_", "-", "2013", "13", "21"]

def gen_candidates(base, big=False):
    seen = set()
    def emit(c):
        if c and c not in seen:
            seen.add(c); return True
        return False
    out = []
    # 1) word forms x prefixes x suffixes
    for w in base:
        for f in word_forms(w):
            for pre in PREFIXES:
                for suf in SUFFIXES:
                    c = pre + f + suf
                    if emit(c): out.append(c)
    # 2) combinator: two base words joined
    for w1 in base:
        for w2 in base:
            for sep in SEPS:
                for c in (w1+sep+w2, w1.capitalize()+sep+w2.capitalize(),
                          w1.lower()+sep+w2.lower()):
                    if emit(c): out.append(c)
    # 3) pure masks: wallet-words + numeric tails
    bases = ["billetera","Billetera","BILLETERA","wallet","Wallet",
             "WALLET","monedero","Monedero","cartera"]
    rng = 100000 if big else 10000
    for b in bases:
        for n in range(rng):
            for c in (b+str(n), b+f"{n:04d}"):
                if emit(c): out.append(c)
    return out

# ---------- self test ----------
def selftest():
    """Encrypt a known master key with a known password, then crack it."""
    from os import urandom
    pw = "billetera1969"
    salt = bytes.fromhex("65e1017f33467568")
    iters = 2000  # low for a fast test
    buf = hashlib.sha512(pw.encode() + salt).digest()
    for _ in range(iters - 1):
        buf = hashlib.sha512(buf).digest()
    master = urandom(32)
    cry = AES.new(buf[:32], AES.MODE_CBC, buf[32:48]).encrypt(master + PAD)
    h = f"$bitcoin$96${cry.hex()}$16${salt.hex()}${iters}$2$00$2$00"
    c, s, it = parse_hash(h)
    init_worker(c, s, it)
    assert check("wrongpass") == ("wrongpass", False), "false positive!"
    assert check(pw) == (pw, True), "failed to verify known password!"
    print("[selftest] OK - KDF + AES + padding check are correct.")

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hash", default="hash.txt", help="hash string or file")
    ap.add_argument("--words", default="base_words.txt", help="base words file")
    ap.add_argument("--wordlist", help="optional extra plain wordlist to also try")
    ap.add_argument("--wordlist-only", action="store_true",
                    help="try ONLY --wordlist; skip the generated candidate set")
    ap.add_argument("--big", action="store_true", help="bigger numeric masks (0-99999)")
    ap.add_argument("--procs", type=int, default=cpu_count())
    ap.add_argument("--tried", default="tried.txt",
                    help="file logging every candidate already tried (failed)")
    ap.add_argument("--meta", default="tried_meta.json",
                    help="JSON run summary (counts, status, timestamps)")
    ap.add_argument("--no-resume", action="store_true",
                    help="do NOT skip words listed in the --tried file")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        selftest(); return

    htext = open(args.hash).read() if os.path.exists(args.hash) else args.hash
    cry, salt, iters = parse_hash(htext)
    print(f"[+] iters={iters}  salt={salt.hex()}  procs={args.procs}")

    if args.wordlist_only:
        cands = []
    else:
        base = [l.strip() for l in open(args.words, encoding="utf-8") if l.strip()]
        cands = gen_candidates(base, big=args.big)
    if args.wordlist and os.path.exists(args.wordlist):
        extra = [l.strip() for l in open(args.wordlist, encoding="utf-8", errors="ignore") if l.strip()]
        seen = set(cands)
        cands += [w for w in extra if w not in seen]
    # --- resume: skip anything already tried in a previous run ---
    already = set()
    if not args.no_resume and os.path.exists(args.tried):
        with open(args.tried, encoding="utf-8", errors="ignore") as f:
            already = {l.rstrip("\n") for l in f if l.rstrip("\n")}
        before = len(cands)
        cands = [c for c in cands if c not in already]
        print(f"[+] resume: {len(already):,} words already tried -> skipping "
              f"{before - len(cands):,}")

    total = len(cands)
    print(f"[+] {total:,} unique candidates to try")

    def write_meta(status, found=None, tested=0, elapsed=0.0):
        json.dump({
            "status": status, "found": found,
            "iters": iters, "salt": salt.hex(),
            "tested_this_run": tested,
            "total_tried_recorded": len(already) + tested,
            "elapsed_sec": round(elapsed, 1),
            "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, open(args.meta, "w", encoding="utf-8"), indent=2)

    start = time.time(); done = 0; last = start
    # line-buffered append so the tried-log survives even a hard kill
    tried_f = open(args.tried, "a", buffering=1, encoding="utf-8")
    try:
        with Pool(args.procs, initializer=init_worker, initargs=(cry, salt, iters)) as pool:
            for pw, matched in pool.imap_unordered(check, cands, chunksize=16):
                done += 1
                if matched:
                    el = time.time() - start
                    print(f"\n[!!!] PASSWORD FOUND: {pw!r}   (after {done:,} tries, {el:.0f}s)")
                    found_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "FOUND.txt")
                    with open(found_path, "w", encoding="utf-8") as f:
                        f.write(pw + "\n")
                    write_meta("FOUND", found=pw, tested=done, elapsed=el)
                    pool.terminate(); return
                tried_f.write(pw + "\n")          # record the failed candidate
                now = time.time()
                if now - last >= 5:
                    rate = done / (now - start)
                    eta = (total - done) / rate if rate else 0
                    print(f"  {done:,}/{total:,} ({100*done/total:4.1f}%)  "
                          f"{rate:,.0f}/s  ETA {eta/60:5.1f} min", flush=True)
                    write_meta("running", tested=done, elapsed=now - start)
                    last = now
    finally:
        tried_f.close()
    write_meta("exhausted", tested=done, elapsed=time.time() - start)
    print(f"\n[-] Exhausted {total:,} candidates in {time.time()-start:.0f}s. No match.")
    print(f"    {len(already)+done:,} total words recorded in {args.tried} (won't retry).")
    print("    Next: try a larger wordlist (--wordlist spanish.txt) or --big masks.")

if __name__ == "__main__":
    main()
