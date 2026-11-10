<#
.SYNOPSIS
    One-time setup: writes the CareConnect settings file outside the project.

.DESCRIPTION
    Creates %USERPROFILE%\.careconnect\careconnect.env with the database
    credentials and a freshly generated AI-service API key. Both the Java web
    application (AppConfig) and the Python AI service read this file, so they
    always share the same key, however Tomcat is started (terminal, Eclipse,
    or the VS Code server connector).

    The file is outside the project folder, so it can never be committed.
    Real environment variables still take precedence over the file.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\setup-config.ps1
#>
[CmdletBinding()]
param(
    [string]$DbUser = "root",
    [string]$DbUrl  = "jdbc:mysql://localhost:3306/hospital"
)

$ErrorActionPreference = "Stop"

$dir  = Join-Path $env:USERPROFILE ".careconnect"
$file = Join-Path $dir "careconnect.env"

if (Test-Path $file) {
    $answer = Read-Host "$file already exists. Overwrite it? (y/N)"
    if ($answer -notmatch '^(y|yes)$') {
        Write-Host "Left the existing file unchanged."
        exit 0
    }
}

$enteredUser = Read-Host "MySQL username [$DbUser]"
if (-not [string]::IsNullOrWhiteSpace($enteredUser)) { $DbUser = $enteredUser.Trim() }

$secure = Read-Host "MySQL password for '$DbUser'" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $dbPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

# 32 random bytes -> 64 hex characters
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$rng.Dispose()
$apiKey = -join ($bytes | ForEach-Object { $_.ToString("x2") })

New-Item -ItemType Directory -Force -Path $dir | Out-Null

$content = @"
# CareConnect HMS local settings - DO NOT COMMIT OR SHARE THIS FILE.
# Read by the web application (AppConfig.java) and the AI service (api_server.py).
# Environment variables, when set, take precedence over these values.
HMS_DB_URL=$DbUrl
HMS_DB_USER=$DbUser
HMS_DB_PASSWORD=$dbPassword
HMS_AI_API_URL=http://127.0.0.1:5000
HMS_AI_API_KEY=$apiKey
"@

# A previous run restricted the file's permissions; restore defaults first so it
# can be replaced. (We own the file, so resetting its ACL is always allowed.)
if (Test-Path $file) {
    icacls $file /reset | Out-Null
}

# UTF-8 without BOM, so every reader parses the first line cleanly
[System.IO.File]::WriteAllText($file, $content, (New-Object System.Text.UTF8Encoding($false)))

# Restrict the file to the current user (full control, so later runs can
# overwrite it) plus read access for SYSTEM, in case Tomcat runs as a service.
icacls $file /inheritance:r /grant:r "$($env:USERNAME):(F)" "SYSTEM:(R)" | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Could not restrict the file's permissions (icacls exit code $LASTEXITCODE). The settings were saved anyway."
}

Write-Host ""
Write-Host "Saved settings to $file"
Write-Host "A new AI API key was generated; both services will read it from this file."
Write-Host "Next: scripts\run-ai.bat in one terminal, scripts\run-web.bat in another."
