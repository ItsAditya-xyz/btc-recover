#!/usr/bin/env python3
"""
Decrypt a Bitcoin Core wallet ckey once the password is known.

Bitcoin Core key encryption:
  master_key = SHA512(password + salt) iterated N times  [same KDF as wallet hash]
  IV         = SHA256(SHA256(pubkey))[0:16]
  privkey    = AES-256-CBC-decrypt(master_key[0:32], IV, ckey)[0:32]

Usage:
  python decrypt_key.py --password "yourpassword"
  python decrypt_key.py --password "yourpassword" --ckey <hex> --pubkey <hex>
"""
import argparse, hashlib, sys
from Crypto.Cipher import AES

# ---- wallet hash params (same as hash.txt) ----
SALT_HEX  = "65e1017f33467568"
ITERS     = 63533

# ---- ckey record from wallet.dat ----
DEFAULT_CKEY   = "ed08539535cbec7a75f14820a05c7e52c4e8a30885859e7a43f771f330901f39e74d10e005b4b0aa8240a253885f5b8e"
DEFAULT_PUBKEY = "0200fcf1533b1acf64c345f6488e0c465f781fa6194ea5c3d8f8ee4fd61989ab78"

def derive_master_key(password: str, salt: bytes, iters: int) -> bytes:
    buf = hashlib.sha512(password.encode("utf-8") + salt).digest()
    for _ in range(iters - 1):
        buf = hashlib.sha512(buf).digest()
    return buf[:32]

def hash256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def decrypt_ckey(master_key: bytes, ckey: bytes, pubkey: bytes) -> bytes:
    iv = hash256(pubkey)[:16]
    pt = AES.new(master_key, AES.MODE_CBC, iv).decrypt(ckey)
    return pt[:32]   # strip PKCS7 padding

def to_wif(privkey: bytes, compressed=True) -> str:
    import base64
    payload = b"\x80" + privkey + (b"\x01" if compressed else b"")
    checksum = hash256(payload)[:4]
    data = payload + checksum
    # base58 encode
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n = int.from_bytes(data, "big")
    result = ""
    while n:
        n, r = divmod(n, 58)
        result = alphabet[r] + result
    for b in data:
        if b == 0:
            result = "1" + result
        else:
            break
    return result

def pubkey_from_privkey(privkey: bytes) -> bytes:
    try:
        from Crypto.PublicKey import ECC
        key = ECC.construct(curve="P-256", d=int.from_bytes(privkey, "big"))
    except Exception:
        pass
    # Use secp256k1 via coincurve or ecdsa if available
    try:
        import coincurve
        return coincurve.PublicKey.from_secret(privkey).format(compressed=True)
    except ImportError:
        pass
    try:
        import ecdsa
        sk = ecdsa.SigningKey.from_string(privkey, curve=ecdsa.SECP256k1)
        vk = sk.get_verifying_key()
        x = vk.pubkey.point.x()
        y = vk.pubkey.point.y()
        prefix = b"\x02" if y % 2 == 0 else b"\x03"
        return prefix + x.to_bytes(32, "big")
    except ImportError:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--password", required=True, help="The cracked wallet password")
    ap.add_argument("--ckey",   default=DEFAULT_CKEY,   help="Encrypted private key (hex)")
    ap.add_argument("--pubkey", default=DEFAULT_PUBKEY, help="Public key (hex)")
    ap.add_argument("--salt",   default=SALT_HEX,       help="Salt from hash (hex)")
    ap.add_argument("--iters",  default=ITERS, type=int, help="KDF iterations")
    args = ap.parse_args()

    salt    = bytes.fromhex(args.salt)
    ckey    = bytes.fromhex(args.ckey)
    pubkey  = bytes.fromhex(args.pubkey)

    print(f"[+] Deriving master key ({args.iters:,} iterations)...")
    master_key = derive_master_key(args.password, salt, args.iters)
    print(f"[+] Master key: {master_key.hex()}")

    privkey = decrypt_ckey(master_key, ckey, pubkey)
    print(f"[+] Private key (hex): {privkey.hex()}")

    wif = to_wif(privkey, compressed=True)
    print(f"[+] Private key (WIF): {wif}")

    # Verify decryption is correct by re-deriving pubkey
    derived_pub = pubkey_from_privkey(privkey)
    if derived_pub is not None:
        if derived_pub == pubkey:
            print(f"[+] Pubkey verified ✓ — decryption is correct")
        else:
            print(f"[!] Pubkey MISMATCH — wrong password or wrong ckey/pubkey pair")
            print(f"    Expected : {pubkey.hex()}")
            print(f"    Got      : {derived_pub.hex()}")
    else:
        print(f"[~] Could not verify pubkey (install 'coincurve' or 'ecdsa' to enable)")
        print(f"    pip install ecdsa")

    print()
    print("=== Next steps ===")
    print(f"1. Import WIF key into Electrum: Wallet > Private Keys > Import")
    print(f"   Key: {wif}")
    print(f"2. Or sweep with: electrum sweep {wif} <destination_address>")
    print(f"3. Verify the address matches: 189JveWz2WP79oYU9Gq4NUfiurbiuNPUhn")

if __name__ == "__main__":
    main()
