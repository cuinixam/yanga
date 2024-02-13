# Help
#  Run pyinstaller to build executable.
#  Archive the executable as yanga.windows.amd64.<tag>.zip
#  The <tag> is the latest git tag on remote origin.

# Usage: .\build_exe.ps1
# Example: .\build_exe.ps1

# Fetch the latest git tag from remote origin
git fetch --tags

# Get the latest git tag
$tag = git describe --tags --abbrev=0
Write-Host "Latest git tag: $tag"

# Build the executable by running pyinstaller with poetry from the .venv/Scripts/poetry
$poetry = ".\.venv\Scripts\poetry"
& $poetry run pyinstaller build_exe.spec

# Archive the executable
$tag = $tag -replace "v", ""
$zip = "dist\yanga-$tag-windows-amd64.zip"
Compress-Archive -Path "dist\yanga.exe" -DestinationPath $zip
Write-Host "Archive created: $zip"
