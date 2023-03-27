<#
.DESCRIPTION
    Bootstrap script for installing scoop and the configured packages in 'scoopfile.json'.
    This script was created based on https://github.com/avengineers/bootstrap
#>

[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSReviewUnusedParameter', '', Justification = 'Used in global scope in Main function')]


# About preference variables: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_preference_variable
# Stop execution on first non-terminating error (an error that doesn't stop the cmdlet processing)
$ErrorActionPreference = "Stop"


Function Edit-Env {
    # workaround for GithubActions
    if ($Env:USER_PATH_FIRST -eq "true") {
        $Env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    }
    else {
        $Env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    }
}

Function Invoke-CommandLine {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingInvokeExpression', '', Justification = 'Usually this statement must be avoided (https://learn.microsoft.com/en-us/powershell/scripting/learn/deep-dives/avoid-using-invoke-expression?view=powershell-7.3), here it is OK as it does not execute unknown code.')]
    param (
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$CommandLine,
        [Parameter(Mandatory = $false, Position = 1)]
        [bool]$StopAtError = $true,
        [Parameter(Mandatory = $false, Position = 2)]
        [bool]$Silent = $false
    )
    if (-Not $Silent) {
        Write-Output "Executing: $CommandLine"
    }
    $global:LASTEXITCODE = 0
    Invoke-Expression $CommandLine
    if ($global:LASTEXITCODE -ne 0) {
        if ($StopAtError) {
            Write-Error "Command line call `"$CommandLine`" failed with exit code $global:LASTEXITCODE"
        }
        else {
            if (-Not $Silent) {
                Write-Output "Command line call `"$CommandLine`" failed with exit code $global:LASTEXITCODE, continuing ..."
            }
        }
    }
}

Function Install-Scoop {
    if (Test-Path -Path 'scoopfile.json') {
        Write-Output "File 'scoopfile.json' found, installing scoop and running 'scoop import' ..."
        # Initial Scoop installation
        if (-Not (Get-Command 'scoop' -ErrorAction SilentlyContinue)) {
            Invoke-RestMethod 'https://raw.githubusercontent.com/xxthunder/ScoopInstall/master/install.ps1' -outfile "$PSScriptRoot\bootstrap.scoop.ps1"
            if ((New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
                & $PSScriptRoot\bootstrap.scoop.ps1 -RunAsAdmin
            }
            else {
                & $PSScriptRoot\bootstrap.scoop.ps1
            }
            Edit-Env
        }

        # install needed tools
        Invoke-CommandLine "scoop update"
        Invoke-CommandLine "scoop install lessmsi" -Silent $true

        # Some old tweak to get 7zip installed correctly
        Invoke-CommandLine "scoop config use_lessmsi $true" -Silent $true

        # avoid deadlocks while updating scoop buckets
        Invoke-CommandLine "scoop config autostash_on_conflict $true" -Silent $true

        # some prerequisites to install other packages
        Invoke-CommandLine "scoop install 7zip" -Silent $true
        Invoke-CommandLine "scoop install innounp" -StopAtError $false -Silent $true
        Invoke-CommandLine "scoop install dark" -Silent $true
        Invoke-CommandLine "scoop import scoopfile.json"
        Edit-Env
    }
    else {
        Write-Output "File 'scoopfile.json' not found, skipping Scoop setup."
    }
}

## start of script
Install-Scoop
## end of script
