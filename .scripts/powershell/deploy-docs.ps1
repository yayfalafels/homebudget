Write-Host "Deploying docs to GitHub Pages..." -ForegroundColor Green

mkdocs gh-deploy --force
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to deploy docs" -ForegroundColor Red
    exit 1
}

Write-Host "Docs deployed successfully!" -ForegroundColor Green
