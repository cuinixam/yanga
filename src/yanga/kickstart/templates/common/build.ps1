<#
.DESCRIPTION
    Wrapper for installing dependencies
#>

param(
    [Parameter(Mandatory = $false, HelpMessage = 'Install all dependencies required to build. (Switch, default: false)')]
    [switch]$install = $false,
    [Parameter(Mandatory = $false, HelpMessage = 'Start Visual Studio Code. (Switch, default: false)')]
    [switch]$startVSCode = $false,
    [Parameter(Mandatory = $false, HelpMessage = 'Clean build, wipe out all build artifacts. (Switch, default: false)')]
    [switch]$clean = $false,
    [Parameter(Mandatory = $false, HelpMessage = 'Command to be executed (String)')]
    [string]$command = ""
)

function Remove-Path {
    param (
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$path
    )
    if (Test-Path -Path $path -PathType Container) {
        Write-Output "Deleting directory '$path' ..."
        Remove-Item $path -Force -Recurse
    }
    elseif (Test-Path -Path $path -PathType Leaf) {
        Write-Output "Deleting file '$path' ..."
        Remove-Item $path -Force
    }
}

function Get-User-Menu-Selection {
    Clear-Host
    Write-Information -Tags "Info:" -MessageData "None of the following command line options was given:"
    Write-Information -Tags "Info:" -MessageData ("(1) -install: installation of mandatory dependencies")
    Write-Information -Tags "Info:" -MessageData ("(2) -startVSCode: start Visual Studio Code")
    Write-Information -Tags "Info:" -MessageData ("(3) quit: exit script")
    return(Read-Host "Please make a selection")
}

function Invoke-Bootstrap {
    # Download bootstrap scripts from external repository
    Invoke-RestMethod -Uri https://raw.githubusercontent.com/avengineers/bootstrap-installer/v1.19.0/install.ps1 | Invoke-Expression
    # Execute bootstrap script
    . .\.bootstrap\bootstrap.ps1
}

## start of script
# Always set the $InformationPreference variable to "Continue" globally,
# this way it gets printed on execution and continues execution afterwards.
$InformationPreference = "Continue"

# Stop on first error
$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot
Write-Output "Running in ${pwd}"

try {
    if ((-Not $install) -and (-Not $startVSCode)) {
        $selectedOption = Get-User-Menu-Selection

        switch ($selectedOption) {
            '1' {
                Write-Information -Tags "Info:" -MessageData "Installing mandatory dependencies ..."
                $install = $true
            }
            '2' {
                Write-Information -Tags "Info:" -MessageData "Starting VS Code ..."
                $startVSCode = $true
            }
            default {
                Write-Information -Tags "Info:" -MessageData "Nothing selected."
                exit
            }
        }
    }

    if ($clean) {
        Remove-Path ".venv"
        Remove-Path ".yanga"
    }

    if ($install) {
        # bootstrap environment
        Invoke-Bootstrap
    }

    # Load bootstrap's utility functions
    . .\.bootstrap\utils.ps1


    Invoke-CommandLine ".venv\Scripts\yanga run --step GenerateEnvSetupScript --not-interactive"

    # Load environment setup script
    . .\.yanga\build\install\env_setup.ps1

    if ($startVSCode) {
        Write-Output "Starting Visual Studio Code..."
        Invoke-CommandLine "code ." -StopAtError $false
    }

    if ($command -ne "") {
        Write-Output "Executing command: $command"
        Invoke-CommandLine $command
    }
}
finally {
    Pop-Location
}
## end of script
