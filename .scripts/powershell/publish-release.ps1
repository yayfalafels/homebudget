param(
    [Parameter(Mandatory=$true)]
    [string]$tag
)

Write-Host "Publishing release with tag: $tag" -ForegroundColor Green

# Verify tag format (should start with 'v')
if (-not $tag.StartsWith('v')) {
    Write-Host "Error: Tag must start with 'v' (e.g., v2.1.1)" -ForegroundColor Red
    exit 1
}

# Create git tag
Write-Host "Creating git tag..." -ForegroundColor Cyan
git tag $tag
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to create git tag" -ForegroundColor Red
    exit 1
}

# Push tag to origin
Write-Host "Pushing tag to origin..." -ForegroundColor Cyan
git push origin $tag
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to push tag to origin" -ForegroundColor Red
    exit 1
}

Write-Host "Release published successfully!" -ForegroundColor Green
Write-Host "GitHub Actions will automatically build and create the release." -ForegroundColor Yellow
