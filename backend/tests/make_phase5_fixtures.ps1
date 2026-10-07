# Synthetic test records only. No external images or citizen information.
Add-Type -AssemblyName System.Drawing
$fixtureRoot = Join-Path $PSScriptRoot 'fixtures/phase5'
New-Item -ItemType Directory -Path $fixtureRoot -Force | Out-Null
$records = @{
    financial = @('SYNTHETIC PAYMENT RECORD', 'Amount: INR 3,500.00', 'Payment method: UPI', 'Transaction reference: SYNTH-UTR-3500', 'Status: Completed', 'Recipient: Sample Store', 'Recipient UPI: sample-store@upi', 'Date: 07 October (year not shown)')
    threat = @('SYNTHETIC NON-EXPLICIT CHAT', 'Platform: Instagram', 'Profile: https://example.invalid/profile/demo', 'Message: Pay me or I will share your private photos.', 'No photos or explicit media included.', 'Time shown: 10:30 (date and timezone not shown)')
    account = @('SYNTHETIC ACCOUNT NOTICE', 'Platform: Google', 'Profile: demo@example.invalid', 'Message: An unfamiliar device signed in.', 'Time shown: 08:15 (date and timezone not shown)')
}
foreach ($name in $records.Keys) {
    $bitmap = New-Object System.Drawing.Bitmap(1100,650)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.Clear([System.Drawing.Color]::White)
    $font = New-Object System.Drawing.Font('Arial',18)
    $row = 0
    foreach ($line in $records[$name]) {
        $graphics.DrawString($line,$font,[System.Drawing.Brushes]::Black,35,(35+$row*55))
        $row++
    }
    $bitmap.Save((Join-Path $fixtureRoot "$name.png"),[System.Drawing.Imaging.ImageFormat]::Png)
    if ($name -eq 'financial') {
        $bitmap.Save((Join-Path $fixtureRoot 'financial.jpg'),[System.Drawing.Imaging.ImageFormat]::Jpeg)
    }
    $font.Dispose()
    $graphics.Dispose()
    $bitmap.Dispose()
}
Write-Output 'Synthetic PNG/JPEG fixtures generated.'
