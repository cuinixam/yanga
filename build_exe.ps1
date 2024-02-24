# Help
#  Run pyinstaller to build executable.
#  Archive the executable as yanga.windows.amd64.<tag>.zip
#  The <tag> is the latest git tag on remote origin.

# Fetch the latest git tag from remote origin
git fetch --tags

# Get the tag of the current commit (HEAD)
$tag = git tag --contains HEAD
Write-Host "Tag of the current commit: $tag"

# Check if the tag matches the version pattern v*.*.*
if ($tag -match "v\d+\.\d+\.\d+") {
    # Build the executable by running pyinstaller with poetry from the .venv/Scripts/poetry
    $poetry = ".\.venv\Scripts\poetry"
    & $poetry run pyinstaller build_exe.spec

    # Archive the executable
    $tag = $tag -replace "v", ""
    $zip = "dist\yanga-$tag-windows-amd64.zip"
    Compress-Archive -Path "dist\yanga\*" -DestinationPath $zip
    Write-Host "Archive created: $zip"
} else {
    Write-Host "The current commit does not have a version tag v*.*.*"
}
