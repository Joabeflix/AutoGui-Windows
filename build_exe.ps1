$ErrorActionPreference = "Stop"

$projeto = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projeto

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onedir `
  --windowed `
  --icon "assets\\logo.ico" `
  --name "AutomacaoVisual" `
  main.py

$destinoAutomacoes = Join-Path $projeto "dist\AutomacaoVisual\automacoes"
if (Test-Path $destinoAutomacoes) {
  Remove-Item -Recurse -Force $destinoAutomacoes
}

Copy-Item -Recurse -Force (Join-Path $projeto "automacoes") $destinoAutomacoes

$destinoAssets = Join-Path $projeto "dist\AutomacaoVisual\assets"
if (Test-Path $destinoAssets) {
  Remove-Item -Recurse -Force $destinoAssets
}

Copy-Item -Recurse -Force (Join-Path $projeto "assets") $destinoAssets

Write-Host "Build concluido em dist\AutomacaoVisual"
