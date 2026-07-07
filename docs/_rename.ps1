Copy-Item 'C:\Users\12977\Desktop\GEO-Product-customer.docx' -Destination 'C:\Users\12977\Desktop\GEO-产品介绍-客户版.docx' -Force
Remove-Item 'C:\Users\12977\Desktop\GEO-Product-customer.docx' -Force
Get-ChildItem 'C:\Users\12977\Desktop\GEO*.docx' | Select-Object Name, Length
