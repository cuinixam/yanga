<#
.DESCRIPTION
    Wrapper for installing dependencies
#>

function Invoke-Bootstrap {
    # Download bootstrap scripts from external repository
    Invoke-RestMethod https://raw.githubusercontent.com/avengineers/bootstrap-installer/v1.17.0/install.ps1 | Invoke-Expression
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
    # bootstrap environment
    Invoke-Bootstrap
    # Load bootstrap's utility functions
    . .\.bootstrap\utils.ps1

    Invoke-CommandLine ".venv\Scripts\pypeline run --config-file yanga.yaml --step GenerateEnvSetupScript"
}
finally {
    Pop-Location
}
## end of script
