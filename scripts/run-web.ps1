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
$javac = Get-Command javac -ErrorAction SilentlyContinue
if (-not $javac) {
    Fail "javac not found. Install JDK 21 and make sure its bin folder is on PATH."
}
# catalina.bat refuses to start without JAVA_HOME or JRE_HOME. If neither is
# set, ask Java where it is installed. (javac's own folder is not reliable:
# Oracle's installer puts a "javapath" shortcut folder on PATH.)
if (-not $env:JAVA_HOME -and -not $env:JRE_HOME) {
    $javaExe = Join-Path (Split-Path -Parent $javac.Source) "java.exe"
    # The settings are printed on stderr; under "Stop", PowerShell 5.1 would
    # treat each stderr line as a terminating error, so relax it briefly.
    $prevPref = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $homeLine = & $javaExe -XshowSettings:properties -version 2>&1 |
                ForEach-Object { "$_" } |
                Where-Object { $_ -match '^\s*java\.home\s*=' } | Select-Object -First 1
    $ErrorActionPreference = $prevPref
    if ($homeLine) {
        $env:JAVA_HOME = ($homeLine -split '=', 2)[1].Trim()
    } else {
        $env:JAVA_HOME = Split-Path -Parent (Split-Path -Parent $javac.Source)
    }
}
Write-Host "Java:    $(if ($env:JAVA_HOME) { $env:JAVA_HOME } else { $env:JRE_HOME })"

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
