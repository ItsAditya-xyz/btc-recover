# Phase 2: Wordlist-only runs
# Safe to stop and restart at any time:
#   - Completed phases are skipped (done/<phase>.done marker files)
#   - Mid-phase runs resume via their --tried log (no repeats)

$hash = "d:\Bounties\Findings\hash.txt"
$wl   = "d:\Bounties\Findings\wordlists"
$done = "d:\Bounties\Findings\wordlists\done"
New-Item -ItemType Directory -Path $done -Force | Out-Null

function Check-Found {
    if (Test-Path "d:\Bounties\Findings\FOUND.txt") {
        Write-Output "`n[!!!] FOUND.txt exists - password cracked! Stopping."
        exit 0
    }
}

function Run-Phase {
    param($label, $marker, $wordlist, $tried, $meta)
    $markerFile = "$done\$marker.done"
    if (Test-Path $markerFile) {
        Write-Output "`n=== $label - already completed, skipping ==="
        return
    }
    Write-Output "`n=== $label ==="
    python d:\Bounties\Findings\recover.py `
        --hash $hash `
        --wordlist-only --wordlist $wordlist `
        --tried $tried --meta $meta
    Check-Found
    # Only mark done if exhausted (no FOUND.txt = no match = fully tried)
    New-Item -ItemType File -Path $markerFile -Force | Out-Null
    Write-Output "  [marked complete: $marker]"
}

Run-Phase "Phase 2a: Spanish dictionary (71k words)  ~16 min" `
    "spanish" "$wl\spanish.txt" "$wl\tried_spanish.txt" "$wl\meta_spanish.json"

Run-Phase "Phase 2b: rockyou top 75% (59k passwords)  ~13 min" `
    "rk75" "$wl\rockyou_top75pct.txt" "$wl\tried_rk75.txt" "$wl\meta_rk75.json"

Run-Phase "Phase 2c: 10k most common passwords  ~3 min" `
    "10k" "$wl\common_10k.txt" "$wl\tried_10k.txt" "$wl\meta_10k.json"

Run-Phase "Phase 2d: Full rockyou part 1 (7.1M passwords)  ~27 hrs" `
    "rockyou_p1" "$wl\rockyou_part1.txt" "$wl\tried_rockyou.txt" "$wl\meta_rockyou_p1.json"

Run-Phase "Phase 2e: Full rockyou part 2 (7.1M passwords)  ~27 hrs" `
    "rockyou_p2" "$wl\rockyou_part2.txt" "$wl\tried_rockyou.txt" "$wl\meta_rockyou_p2.json"

Write-Output "`nAll Phase 2 wordlists exhausted. No match."
Write-Output "Next: cloud GPU + hashcat -m 11300, or btcrecover with a tokenlist."
