$desktop = [Environment]::GetFolderPath('Desktop')
Get-Process WINWORD -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$html = 'c:\Users\12977\Desktop\GEO\_customer.html'
$out = Join-Path $desktop 'GEO-Product-customer.docx'
if (Test-Path $out) { Remove-Item $out -Force }
$doc = $word.Documents.Open($html, $false, $true)
$doc.SaveAs2($out, 16)
$doc.Close($false)
$word.Quit()
$final = Join-Path $desktop 'GEO-产品介绍-客户版.docx'
if (Test-Path $final) { Remove-Item $final -Force }
Move-Item $out $final -Force
Write-Output $final
