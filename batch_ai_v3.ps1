# Slow sequential AI image download
$ua = "Mozilla/5.0 Chrome/120"
$dest = "C:\Users\xuyq\coffee-shop-oms\src\static\img\products".Replace("xuyq", [char]0x8BB8 + "yq")

$products = @(
    @{ file = "brownie.jpg"; seed = 171; prompt = "A chocolate brownie square on white plate, dense fudgy texture, light cocoa powder dusting, professional bakery photography, soft natural light, white wooden table, realistic" }
    @{ file = "madeleine.jpg"; seed = 181; prompt = "French madeleine cakes on wooden serving board, golden brown shell-shaped pattern, powdered sugar dusting, professional bakery photography, warm light, rustic wooden table, realistic" }
    @{ file = "plain-sparkling.jpg"; seed = 191; prompt = "A glass of plain sparkling water with ice cubes, bubbly clear carbonated water, condensation on glass, refreshing, professional drink photography, bright natural light, white background, realistic" }
    @{ file = "lime-sparkling.jpg"; seed = 192; prompt = "A glass of lime sparkling water with fresh lime slices and mint leaves, ice cubes, condensation, bubbles rising, professional drink photography, bright natural light, wooden table, realistic" }
    @{ file = "berry-sparkling.jpg"; seed = 193; prompt = "A glass of pink raspberry sparkling water with fresh raspberries and ice cubes, vibrant pink color, bubbles, condensation, professional drink photography, bright natural light, wooden table, realistic" }
    @{ file = "combo-breakfast.jpg"; seed = 201; prompt = "Breakfast combo americano coffee in white cup and French madeleine cake on white plate, morning sunlight, cafe setting, professional product photography, light wooden table, realistic" }
    @{ file = "combo-afternoon.jpg"; seed = 202; prompt = "Afternoon tea combo hot latte coffee and tiramisu cake slice on wooden tray, cozy cafe, professional product photography, warm light, dark wooden table, realistic" }
    @{ file = "combo-business.jpg"; seed = 203; prompt = "Business power combo double espresso shot in white cup and chocolate brownie square on slate plate, minimalist office cafe, professional product photography, natural light, dark wooden table, realistic" }
    @{ file = "combo-duo.jpg"; seed = 204; prompt = "Friends duo combo two vanilla latte coffees in tall glass mugs and slice of New York cheesecake between them, cheerful cafe, professional product photography, warm natural light, light wooden table, realistic" }
)

foreach ($p in $products) {
    $target = Join-Path $dest $p.file
    if ((Test-Path $target) -and (Get-Item $target).Length -gt 20000) {
        Write-Host "SKIP $($p.file)"
        continue
    }
    $promptEncoded = [System.Uri]::EscapeDataString($p.prompt)
    $url = "https://image.pollinations.ai/prompt/$promptEncoded`?seed=$($p.seed)&width=600&height=600"

    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            Invoke-WebRequest -Uri $url -OutFile $target -UserAgent $ua -TimeoutSec 180 -ErrorAction Stop
            $size = (Get-Item $target).Length
            if ($size -gt 10000) {
                Write-Host "OK $($p.file) ($([math]::Round($size/1024,1)) KB)"
                break
            } else {
                Remove-Item $target -Force -ErrorAction SilentlyContinue
                throw "too small"
            }
        } catch {
            if ($attempt -eq 3) {
                Write-Host "FAIL $($p.file): $_"
            } else {
                Start-Sleep -Seconds 15
            }
        }
    }
    Start-Sleep -Seconds 30  # Long delay between to avoid rate limiting
}
Write-Host "All done"
