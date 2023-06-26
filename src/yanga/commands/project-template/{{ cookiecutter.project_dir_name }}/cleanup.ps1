# Specify the directories to delete, relative to the script's directory
$directoriesToDelete = @(".venv", "build", ".yanga")

# Get this script's directory
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path

foreach ($directory in $directoriesToDelete) {
    $directoryPath = Join-Path -Path $scriptDirectory -ChildPath $directory

    # Delete the directory
    if (Test-Path -Path $directoryPath) {
        try {
            Remove-Item -Path $directoryPath -Recurse -Force -ErrorAction Stop
            Write-Host "The '$directory' directory has been deleted."
        }
        catch {
            Write-Host "Failed to delete the '$directory' directory. Please make sure all files are closed in that directory and try again."
        }
    }
}
