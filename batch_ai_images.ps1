# Batch download AI-generated product images from Pollinations
$ua = "Mozilla/5.0 Chrome/120"
$dest = "C:\Users\xuyq\coffee-shop-oms\src\static\img\products".Replace("xuyq", [char]0x8BB8 + "yq")

$products = @(
    @{ file = "jasmine-tea.jpg"; seed = 51; prompt = "A cup of jasmine tea with delicate floral notes, light golden tea in a small white porcelain teacup on saucer, fresh jasmine flowers garnish on the side, professional product photography, soft natural light, light wooden table, realistic" }
    @{ file = "coconut-cold-brew.jpg"; seed = 61; prompt = "An iced coconut cold brew coffee in a tall clear glass with ice cubes, dark cold brew coffee mixed with creamy coconut milk creating layers, fresh coconut chunks beside the glass, professional coffee shop product photography, warm natural light, wooden cafe table, realistic" }
    @{ file = "brownie.jpg"; seed = 71; prompt = "A single rich chocolate brownie square on a small white plate, dense fudgy texture, light dusting of cocoa powder on top, fork beside, professional bakery product photography, soft natural light, white wooden table, realistic" }
    @{ file = "madeleine.jpg"; seed = 81; prompt = "Several shell-shaped French madeleine cakes on a wooden serving board, golden brown with characteristic ridged shell pattern, light dusting of powdered sugar, professional bakery product photography, warm soft light, rustic wooden table, realistic" }
    @{ file = "plain-sparkling.jpg"; seed = 91; prompt = "A glass of plain sparkling soda water with ice cubes, clear bubbly carbonated water, condensation droplets on the glass, simple and refreshing, professional drink product photography, bright natural light, white minimal background, realistic" }
    @{ file = "lime-sparkling.jpg"; seed = 92; prompt = "A glass of lime sparkling water with fresh lime slices and mint leaves, ice cubes, condensation on the clear glass, bubbles rising, professional drink product photography, bright natural light, light wooden table, realistic" }
    @{ file = "berry-sparkling.jpg"; seed = 93; prompt = "A glass of pink raspberry sparkling water with fresh raspberries and ice cubes, vibrant pink color, bubbles visible, condensation on the glass, professional drink product photography, bright natural light, light wooden table, realistic" }
    @{ file = "combo-breakfast.jpg"; seed = 101; prompt = "A breakfast combo with a hot americano coffee and a French madeleine cake on a white plate, morning sunlight, cafe setting, professional product photography, light wooden table, realistic" }
    @{ file = "combo-afternoon.jpg"; seed = 102; prompt = "An afternoon tea combo with a hot latte coffee and a slice of tiramisu cake on a wooden tray, cozy cafe setting, professional product photography, soft warm light, dark wooden table, realistic" }
    @{ file = "combo-business.jpg"; seed = 103; prompt = "A business power combo with a double espresso shot in white cup and a single chocolate brownie square on slate plate, minimalist office cafe setting, professional product photography, natural light, dark wooden table, realistic" }
    @{ file = "combo-duo.jpg"; seed = 104; prompt = "A friends duo combo with two vanilla latte coffees in tall glass mugs and one slice of New York cheesecake between them, cheerful cafe setting, professional product photography, warm natural light, light wooden table, realistic" }
)

foreach ($p in $products) {
    $promptEncoded = [System.Uri]::EscapeDataString($p.prompt)
    $url = "https://image.pollinations.ai/prompt/$promptEncoded`?seed=$($p.seed)&width=600&height=600"
    $target = Join-Path $dest $p.file
    try {
        Invoke-WebRequest -Uri $url -OutFile $target -UserAgent $ua -TimeoutSec 90 -ErrorAction Stop
        $kb = [math]::Round((Get-Item $target).Length/1024, 1)
        Write-Host "OK $($p.file) ($kb KB)"
    } catch {
        Write-Host "FAIL $($p.file): $_"
    }
}
