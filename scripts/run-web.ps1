<#
.SYNOPSIS
    Compiles the web application, deploys it to Tomcat and starts Tomcat.

.DESCRIPTION
    The project has no Maven/Gradle build, so this script does the build:
      1. compiles src/main/java (excluding com/hms/test) into build/classes
      2. copies src/main/webapp + the classes into <Tomcat>/webapps/<ContextName>
      3. runs Tomcat in this window (Ctrl+C to stop)

    Settings (database credentials, AI key) come from environment variables or
    from %USERPROFILE%\.careconnect\careconnect.env - run scripts\setup-config.ps1
    once to create that file.

.PARAMETER TomcatHome
    Tomcat folder (the one containing bin\catalina.bat). If omitted, uses
    CATALINA_HOME, then searches your user folder for apache-tomcat-10.*.

.PARAMETER ContextName
    Web application name in the URL. Default: HospitalManagementSystem.

.PARAMETER NoStart
    Build and deploy only; don't start Tomcat (use this when Tomcat is already
    running, e.g. from the VS Code server connector - it reloads automatically).

.EXAMPLE
    scripts\run-web.bat
    scripts\run-web.bat -NoStart
    scripts\run-web.bat -TomcatHome "C:\tools\apache-tomcat-10.1.57"
#>
[CmdletBinding()]
param(
    [string]$TomcatHome,
    [string]$ContextName = "HospitalManagementSystem",
    [switch]$NoStart
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Fail([string]$msg) {
    Write-Host "ERROR: $msg" -ForegroundColor Red
    exit 1
}

# --- locate Tomcat -----------------------------------------------------------
if (-not $TomcatHome -and $env:CATALINA_HOME) { $TomcatHome = $env:CATALINA_HOME }
if (-not $TomcatHome) {
    $found = Get-ChildItem -Path $env:USERPROFILE -Filter catalina.bat -Recurse -Depth 4 -ErrorAction SilentlyContinue |
             Where-Object { $_.FullName -match 'apache-tomcat-10' -and $_.Directory.Name -eq 'bin' } |
             Select-Object -First 1
    if ($found) { $TomcatHome = $found.Directory.Parent.FullName }
}
if (-not $TomcatHome -or -not (Test-Path (Join-Path $TomcatHome "bin\catalina.bat"))) {
    Fail "Tomcat 10.1 not found. Pass -TomcatHome <folder containing bin\catalina.bat>."
}
Write-Host "Tomcat:  $TomcatHome"

# --- check the JDK -----------------------------------------------------------
if (-not (Get-Command javac -ErrorAction SilentlyContinue)) {
    Fail "javac not found. Install JDK 21 and make sure its bin folder is on PATH."
}

# --- compile -----------------------------------------------------------------
$classes = Join-Path $root "build\classes"
if (Test-Path $classes) { Remove-Item -Recurse -Force $classes }
New-Item -ItemType Directory -Force $classes | Out-Null

$sources = Get-ChildItem -Recurse (Join-Path $root "src\main\java") -Filter *.java |
           Where-Object { $_.FullName -notmatch '\\com\\hms\\test\\' } |
           ForEach-Object { $_.FullName }
$argFile = Join-Path $env:TEMP "careconnect-sources.txt"
$sources | ForEach-Object { '"' + ($_ -replace '\\', '/') + '"' } | Set-Content -Encoding ASCII $argFile

Write-Host "Compiling $($sources.Count) source files..."
& javac -encoding UTF-8 -d $classes -cp "src\main\webapp\WEB-INF\lib\*" "@$argFile"
if ($LASTEXITCODE -ne 0) { Fail "Compilation failed (see errors above)." }

# --- deploy ------------------------------------------------------------------
$app = Join-Path $TomcatHome "webapps\$ContextName"
Write-Host "Deploying to $app"
# The servlet API jar is compile-only; Tomcat provides its own at runtime.
robocopy "src\main\webapp" $app /E /XF jakarta.servlet-api-6.0.0.jar /XD classes /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { Fail "Copying web files failed (robocopy exit code $LASTEXITCODE)." }
robocopy $classes (Join-Path $app "WEB-INF\classes") /E /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { Fail "Copying classes failed (robocopy exit code $LASTEXITCODE)." }

$cfg = Join-Path $env:USERPROFILE ".careconnect\careconnect.env"
if (-not $env:HMS_DB_USER -and -not (Test-Path $cfg)) {
    Write-Host "WARNING: no database settings found. Run scripts\setup-config.ps1 first," -ForegroundColor Yellow
    Write-Host "         or every page will show empty data and sign-in will fail." -ForegroundColor Yellow
}

$url = "http://localhost:8080/$ContextName/"
if ($NoStart) {
    Write-Host "Deployed. A running Tomcat reloads it within a few seconds: $url" -ForegroundColor Green
    exit 0
}

Write-Host "Starting Tomcat. Open $url  (Ctrl+C to stop)" -ForegroundColor Green
$env:CATALINA_HOME = $TomcatHome
& (Join-Path $TomcatHome "bin\catalina.bat") run
