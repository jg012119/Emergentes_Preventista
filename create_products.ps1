$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyOWU1ZGRkMi1lNDZlLTRhYWQtOGJhYi0yMGMxMWRkY2M2ZjYiLCJlbWFpbCI6ImFnZW50MUBleGFtcGxlLmNvbSIsImV4cCI6MTc4MDI5MDQzOX0.W4E19YMB8b6CLo_zxhNR5Mm2eZrbFzk5QB7pIU4O6Ok"
$products = @(
    @{name="Cocalo Cola"; category="Bebida"; price=5.0; stock=200},
    @{name="Aguar Limonada"; category="Bebida"; price=4.5; stock=150},
    @{name="Oro Refresco"; category="Bebida"; price=6.0; stock=180},
    @{name="Cocalas Energía"; category="Energizante"; price=7.5; stock=100},
    @{name="Aguar Fruta"; category="Bebida"; price=5.5; stock=120}
)
foreach ($p in $products) {
    $body = $p | ConvertTo-Json -Depth 5
    try {
        $resp = Invoke-RestMethod -Uri http://127.0.0.1:8000/products/ -Method Post -Headers @{ Authorization = "Bearer $token" } -ContentType "application/json" -Body $body
        Write-Host "Created:" $resp.id $resp.name
    } catch {
        Write-Host "Error creating product:" $_.Exception.Message
    }
}
