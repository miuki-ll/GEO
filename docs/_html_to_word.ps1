$desktop = [Environment]::GetFolderPath('Desktop')
$word = New-Object -ComObject Word.Application
$word.Visible = $false

function Convert-HtmlToDocx($htmlPath, $docxPath) {
    if (Test-Path $docxPath) { Remove-Item $docxPath -Force }
    $doc = $word.Documents.Open($htmlPath, $false, $true, $false, "utf-8")
    $doc.SaveAs2($docxPath, 16)
    $doc.Close($false)
}

Convert-HtmlToDocx 'c:\Users\12977\Desktop\GEO\_prd.html' (Join-Path $desktop 'GEO-PRD-tech.docx')
Convert-HtmlToDocx 'c:\Users\12977\Desktop\GEO\_customer.html' (Join-Path $desktop 'GEO-Product-customer.docx')

$word.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null

# Rename to Chinese filenames
$final1 = Join-Path $desktop 'GEO-PRD-技术版.docx'
$final2 = Join-Path $desktop 'GEO-产品介绍-客户版.docx'
if (Test-Path $final1) { Remove-Item $final1 -Force }
if (Test-Path $final2) { Remove-Item $final2 -Force }
Move-Item (Join-Path $desktop 'GEO-PRD-tech.docx') $final1 -Force
Move-Item (Join-Path $desktop 'GEO-Product-customer.docx') $final2 -Force

Write-Output $final1
Write-Output $final2
