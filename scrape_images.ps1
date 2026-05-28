# Batch scrape Unsplash for product images
$ErrorActionPreference = "SilentlyContinue"
$ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
$candDir = "C:\Users\xuyq\coffee-shop-oms\_candidates"
$candDir = $candDir.Replace("xuyq", [char]0x8BB8 + "yq")
New-Item -ItemType Directory -Force -Path $candDir | Out-Null

$queries = @{
    "espresso"          = "espresso-coffee-cup"
    "americano"         = "americano-black-coffee"
    "iced-americano"    = "iced-americano-coffee"
    "double-espresso"   = "double-espresso-shot"
    "latte"             = "cafe-latte-cup"
    "iced-latte"        = "iced-latte-glass"
    "oat-latte"         = "oat-milk-latte"
    "vanilla-latte"     = "vanilla-latte"
    "cappuccino"        = "cappuccino-cup"
    "flat-white"        = "flat-white-coffee"
    "mocha"             = "mocha-coffee"
    "caramel-macchiato" = "caramel-macchiato"
    "earl-grey-tea"     = "earl-grey-tea-cup"
    "matcha-latte"      = "matcha-latte"
    "jasmine-tea"       = "jasmine-tea-cup"
    "cold-brew"         = "cold-brew-coffee"
    "coconut-cold-brew" = "coconut-coffee-iced"
    "iced-lemon-tea"    = "iced-lemon-tea"
    "tiramisu"          = "tiramisu-dessert"
    "cheesecake"        = "new-york-cheesecake"
    "brownie"           = "chocolate-brownie"
    "madeleine"         = "madeleine-cake-french"
    "plain-sparkling"   = "sparkling-water-glass"
    "lime-sparkling"    = "lime-soda-water"
    "berry-sparkling"   = "berry-soda-pink"
    "combo-breakfast"   = "coffee-breakfast-pastry"
    "combo-afternoon"   = "afternoon-tea-coffee-cake"
    "combo-business"    = "espresso-dessert"
    "combo-duo"         = "two-coffee-cups"
}

foreach ($key in $queries.Keys) {
    $q = $queries[$key]
    $url = "https://unsplash.com/s/photos/$q"
    Write-Host "Searching $key ($q)..." -NoNewline

    try {
        $resp = Invoke-WebRequest -Uri $url -UserAgent $ua -TimeoutSec 25 -ErrorAction Stop
        $html = $resp.Content
        $regexMatches = [regex]::Matches($html, 'images\.unsplash\.com/photo-([a-f0-9]+-[a-f0-9]+)')
        $ids = $regexMatches | ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique | Select-Object -First 5

        if ($ids.Count -eq 0) {
            Write-Host " no IDs found"
            continue
        }

        $folder = Join-Path $candDir $key
        New-Item -ItemType Directory -Force -Path $folder | Out-Null

        $idx = 1
        foreach ($id in $ids) {
            $imgUrl = "https://images.unsplash.com/photo-$id" + "?w=600&q=80"
            $outFile = Join-Path $folder "$idx.jpg"
            try {
                Invoke-WebRequest -Uri $imgUrl -OutFile $outFile -UserAgent $ua -TimeoutSec 20 -ErrorAction Stop
                $size = (Get-Item $outFile).Length
                if ($size -lt 5000) {
                    Remove-Item $outFile
                } else {
                    $idx++
                }
            } catch {}
        }
        $count = $idx - 1
        Write-Host " got $count images"
    } catch {
        Write-Host " FAILED"
    }
}

Write-Host ""
Write-Host "Done. Output: $candDir"
