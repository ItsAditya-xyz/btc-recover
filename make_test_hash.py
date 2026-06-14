#!/usr/bin/env python3
"""Produce a real-format $bitcoin$ hash for a KNOWN password, exactly like a
Bitcoin Core wallet.dat encrypted with that password would yield via bitcoin2john.
Usage: python make_test_hash.py <password> [iterations]"""
import sys, hashlib
from os import urandom
from Crypto.Cipher import AES

PAD = b"\x10" * 16
pw = sys.argv[1] if len(sys.argv) > 1 else "billetera2013"
iters = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
salt = urandom(8)
buf = hashlib.sha512(pw.encode() + salt).digest()
for _ in range(iters - 1):
    buf = hashlib.sha512(buf).digest()
master = urandom(32)                       # the 32-byte wallet master key
cry = AES.new(buf[:32], AES.MODE_CBC, buf[32:48]).encrypt(master + PAD)
print(f"$bitcoin$96${cry.hex()}$16${salt.hex()}${iters}$2$00$2$00")
