# Salin aplikasi Flask dari E:\Project\UMKM ke folder apps\ (tanpa venv, database, tes).
# Jalankan lagi setiap kali proyek aslinya berubah:  .\sync_apps.ps1
$src = "E:\Project\UMKM"
$map = @{ "3-katering-flask" = "katering"; "4-inventory-flask" = "stokku" }
foreach ($k in $map.Keys) {
  $dst = Join-Path $PSScriptRoot "apps\$($map[$k])"
  if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
  robocopy "$src\$k" $dst /E /XD .venv __pycache__ /XF *.db *.pyc test_app.py Procfile render.yaml wsgi.py seed.py README.md .gitignore | Out-Null
  Write-Host "disalin: $k -> apps\$($map[$k])"
}
