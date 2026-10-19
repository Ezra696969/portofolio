# Salin aplikasi dari folder proyek asli ke apps\ (tanpa venv, database, tes).
# Jalankan lagi setiap kali proyek aslinya berubah:  .\sync_apps.ps1
$umkm = "E:\Project\UMKM"
$map = @{ "3-katering-flask" = "katering"; "4-inventory-flask" = "stokku" }
foreach ($k in $map.Keys) {
  $dst = Join-Path $PSScriptRoot "apps\$($map[$k])"
  if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
  robocopy "$umkm\$k" $dst /E /XD .venv __pycache__ /XF *.db *.pyc test_app.py Procfile render.yaml wsgi.py seed.py README.md .gitignore | Out-Null
  Write-Host "disalin: $k -> apps\$($map[$k])"
}
# StockLab versi Flask/JS (E:\Project\STOCKLAB-WEB)
$sl = "E:\Project\STOCKLAB-WEB"
$dst = Join-Path $PSScriptRoot "apps\stocklab"
if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
robocopy $sl $dst /E /XD .venv __pycache__ cache_runtime .pytest_cache /XF *.pyc *.err test_web.py run.py requirements.txt README.md | Out-Null
Write-Host "disalin: STOCKLAB-WEB -> apps\stocklab"
