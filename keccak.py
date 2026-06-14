# minimal keccak-256 (Ethereum) pure python
def keccak256(msg: bytes) -> bytes:
    RC=[0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,
        0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,
        0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,
        0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,
        0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,
        0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008]
    R=[[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]]
    def rol(x,n): n%=64; return ((x<<n)|(x>>(64-n)))&0xFFFFFFFFFFFFFFFF
    rate=136 # 1088 bits for keccak-256
    # pad: keccak uses 0x01 domain, then 0x80 at end
    m=bytearray(msg); m.append(0x01)
    while len(m)%rate!=0: m.append(0)
    m[-1]^=0x80
    S=[[0]*5 for _ in range(5)]
    for off in range(0,len(m),rate):
        blk=m[off:off+rate]
        for i in range(rate//8):
            x=i%5; y=i//5
            S[x][y]^=int.from_bytes(blk[i*8:i*8+8],'little')
        for rnd in range(24):
            C=[S[x][0]^S[x][1]^S[x][2]^S[x][3]^S[x][4] for x in range(5)]
            D=[C[(x-1)%5]^rol(C[(x+1)%5],1) for x in range(5)]
            for x in range(5):
                for y in range(5): S[x][y]^=D[x]
            B=[[0]*5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    B[y][(2*x+3*y)%5]=rol(S[x][y],R[x][y])
            for x in range(5):
                for y in range(5):
                    S[x][y]=B[x][y]^((~B[(x+1)%5][y])&B[(x+2)%5][y])
            S[0][0]^=RC[rnd]
    out=b''
    for i in range(rate//8):
        x=i%5;y=i//5
        out+=S[x][y].to_bytes(8,'little')
        if len(out)>=32: break
    return out[:32]

def sel(sig): return keccak256(sig.encode()).hex()[:8]
def topic(sig): return "0x"+keccak256(sig.encode()).hex()

if __name__=="__main__":
    funcs=["processRollup(bytes,bytes)","processRollup(bytes,bytes,bytes)",
           "receiveEthFromBridge(uint256)","depositPendingFunds(uint256,uint256,address,bytes32)",
           "approveProof(bytes32)","offchainData(uint256,uint256,uint256,bytes)"]
    print("== selectors ==")
    for f in funcs: print(" ",sel(f),f)
    evs=["RollupProcessed(uint256,bytes32[],address)","DefiBridgeProcessed(uint256,uint256,uint256,uint256,uint256,bool,bytes)",
         "AsyncDefiBridgeProcessed(uint256,uint256,uint256)","Deposit(uint256,address,uint256)",
         "Withdraw(uint256,address,uint256)","RollupProviderUpdated(address,bool)",
         "FeeDistributed(address,uint256)","Convert(uint256,uint256)","FeeReimbursed(address,uint256)"]
    print("== event topic0 ==")
    for e in evs: print(" ",topic(e),e)
