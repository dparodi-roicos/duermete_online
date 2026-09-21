# push_dashboard.ps1
# Ejecutar después de cada actualización del dashboard en Claude
# Copia el HTML actualizado y lo sube a GitHub Pages

$RepoPath = "C:\Users\Daniela\Downloads\duermete_online"
$SourceHtml = "C:\Users\Daniela\Downloads\duermete_online\index.html"
$Date = Get-Date -Format "yyyy-MM-dd HH:mm"

# Verificar que existe el archivo
if (-not (Test-Path $SourceHtml)) {
    Write-Host "ERROR: No se encontro index.html en $RepoPath" -ForegroundColor Red
    exit 1
}

# Ir al repo y hacer push
Set-Location $RepoPath
git add index.html
git commit -m "Update dashboard: $Date"
git push origin master

Write-Host ""
Write-Host "Dashboard actualizado en GitHub Pages:" -ForegroundColor Green
Write-Host "https://dparodi-roicos.github.io/duermete_online/" -ForegroundColor Cyan
Write-Host ""
