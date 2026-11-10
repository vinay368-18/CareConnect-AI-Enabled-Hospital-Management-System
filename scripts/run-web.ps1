<#
.SYNOPSIS
    Runs the whole CareConnect system with one command: web app + AI service on Tomcat.

.DESCRIPTION
    Usually started from the project folder with:  run.bat

      1. makes sure the settings file exists (%USERPROFILE%\.careconnect\careconnect.env);
         runs the one-time setup if it does not
      2. checks the Python environment for the AI service and installs any
         missing packages from cvd-ai-service\requirements.txt
      3. compiles src/main/java (excluding com/hms/test) into build/classes
      4. copies the web app into <Tomcat>\webapps\<ContextName>
      5. runs Tomcat in this window. The web app starts the AI service itself
         and stops it again when Tomcat stops. Press Ctrl+C to stop everything.

.PARAMETER TomcatHome
    Tomcat folder (the one containing bin\catalina.bat). If omitted, uses
    CATALINA_HOME, then searches your user folder for apache-tomcat-10.*.

.PARAMETER ContextName
    Web application name in the URL. Default: HospitalManagementSystem.

.PARAMETER NoStart
    Build and deploy only; don't start Tomcat (use when Tomcat is already
    running, e.g. from the VS Code server connector - it reloads automatically).

.PARAMETER SkipPythonCheck
    Don't check or install the AI service's Python packages.

.EXAMPLE
    run.bat
    run.bat -NoStart
    run.bat -TomcatHome "C:\tools\apache-tomcat-10.1.57"
#>
[CmdletBinding()]
param(
    [string]$TomcatHome,
    [string]$ContextName = "HospitalManagementSystem",
    [switch]$NoStart,
    [switch]$SkipPythonCheck
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Fail([string]$msg) {
    Write-Host "ERROR: $msg" -ForegroundColor Red
    exit 1
}
function Step([string]$msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

# Runs a native command and returns its combined output as strings. Under
# "Stop", PowerShell 5.1 turns every stderr line into a terminating error.
function Invoke-Native([string]$exe, [string[]]$arguments) {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $out = & $exe @arguments 2>&1 | ForEach-Object { "$_" }
        return @{ Output = $out; ExitCode = $LASTEXITCODE }
    } finally {
        $ErrorActionPreference = $prev
    }
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

# Sets KEY=VALUE in the settings file, replacing an existing line or appending.
function Set-ConfigValue([string]$file, [string]$key, [string]$value) {
    $lines = @()
    if (Test-Path $file) { $lines = @([System.IO.File]::ReadAllLines($file)) }
    $pattern = '^\s*(export\s+)?' + [regex]::Escape($key) + '\s*='
    $found = $false
    $newLines = foreach ($l in $lines) {
        if ($l -match $pattern) { $found = $true; "$key=$value" } else { $l }
    }
    if (-not $found) { $newLines = @($newLines) + "$key=$value" }
    [System.IO.File]::WriteAllText($file, (($newLines -join "`r`n") + "`r`n"), $utf8NoBom)
}

function Get-ConfigValue([string]$file, [string]$key) {
    if (-not (Test-Path $file)) { return $null }
    $pattern = '^\s*(export\s+)?' + [regex]::Escape($key) + '\s*=(.*)$'
    foreach ($l in [System.IO.File]::ReadAllLines($file)) {
        if ($l -match $pattern) { return $Matches[2].Trim().Trim('"').Trim("'") }
    }
    return $null
}

# --- 1. settings -------------------------------------------------------------
Step "Settings"
$cfg = Join-Path $env:USERPROFILE ".careconnect\careconnect.env"
if (-not $env:HMS_DB_USER -and -not (Test-Path $cfg)) {
    Write-Host "No settings yet - running the one-time setup."
    & (Join-Path $PSScriptRoot "setup-config.ps1")
    if (-not (Test-Path $cfg)) { Fail "Setup did not create $cfg." }
}
if (Test-Path $cfg) {
    try { $null = [System.IO.File]::ReadAllText($cfg) }
    catch { Fail "Cannot read $cfg. Run:  icacls `"$cfg`" /reset" }
    Write-Host "    $cfg"
}

# --- 2. Python for the AI service ----------------------------------------------
$serviceDir = Join-Path $root "cvd-ai-service"
Step "AI service (Python)"
$py = $null
if (Test-Path $cfg) { $py = Get-ConfigValue $cfg "HMS_AI_PYTHON" }
if ($py -and -not (Test-Path $py) -and -not (Get-Command $py -ErrorAction SilentlyContinue)) { $py = $null }
if (-not $py) {
    foreach ($candidate in @(
            (Join-Path $serviceDir ".venv\Scripts\python.exe"),
            (Join-Path $serviceDir "venv\Scripts\python.exe"),
            (Join-Path $env:USERPROFILE "cvd-env\Scripts\python.exe"))) {
        if (Test-Path $candidate) { $py = $candidate; break }
    }
}
if (-not $py) {
    $onPath = Get-Command python -ErrorAction SilentlyContinue
    if ($onPath -and $onPath.Source -notmatch 'WindowsApps') {
        # Create a project-local virtual environment rather than installing globally
        Write-Host "    Creating a virtual environment in cvd-ai-service\.venv ..."
        $r = Invoke-Native $onPath.Source @("-m", "venv", (Join-Path $serviceDir ".venv"))
        if ($r.ExitCode -eq 0) { $py = Join-Path $serviceDir ".venv\Scripts\python.exe" }
    }
}

if (-not $py) {
    Write-Host "    WARNING: Python 3.10-3.12 not found. The web app will run, but CVD screening" -ForegroundColor Yellow
    Write-Host "             will show 'AI offline'. Install Python from python.org and re-run." -ForegroundColor Yellow
} else {
    Write-Host "    Python: $py"
    if (-not $SkipPythonCheck) {
        $check = "import importlib.util as u; mods=['fastapi','uvicorn','pydantic','PIL','numpy','torch','torchvision','cv2']; " +
                 "missing=[m for m in mods if u.find_spec(m) is None]; " +
                 "missing += [] if (u.find_spec('python_multipart') or u.find_spec('multipart')) else ['python_multipart']; " +
                 "print(' '.join(missing))"
        $r = Invoke-Native $py @("-c", $check)
        $missing = ($r.Output | Select-Object -Last 1)
        if ($r.ExitCode -ne 0) {
            Write-Host "    WARNING: could not run $py - $($r.Output -join ' ')" -ForegroundColor Yellow
        } elseif ($missing) {
            Write-Host "    Installing missing packages ($missing). The first time this can take several minutes..."
            # Stream pip's progress to the console instead of capturing it
            $prev = $ErrorActionPreference
            $ErrorActionPreference = "Continue"
            & $py -m pip install -r (Join-Path $serviceDir "requirements.txt")
            $pipExit = $LASTEXITCODE
            $ErrorActionPreference = $prev
            if ($pipExit -ne 0) {
                Write-Host "    WARNING: package install failed (see above); the AI service may not start." -ForegroundColor Yellow
            } else {
                Write-Host "    Packages installed."
            }
        } else {
            Write-Host "    Packages OK."
        }
    }
}

# Tell the web app where the AI service and its Python are (it starts them itself)
if (Test-Path $cfg) {
    Set-ConfigValue $cfg "HMS_AI_SERVICE_DIR" $serviceDir
    if ($py) { Set-ConfigValue $cfg "HMS_AI_PYTHON" $py }
}

# --- 3. locate Tomcat and Java -----------------------------------------------------
Step "Tomcat and Java"
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
Write-Host "    Tomcat: $TomcatHome"

$javac = Get-Command javac -ErrorAction SilentlyContinue
if (-not $javac) {
    Fail "javac not found. Install JDK 21 and make sure its bin folder is on PATH."
}
# catalina.bat refuses to start without JAVA_HOME or JRE_HOME. If neither is
# set, ask Java where it is installed. (javac's own folder is not reliable:
# Oracle's installer puts a "javapath" shortcut folder on PATH.)
if (-not $env:JAVA_HOME -and -not $env:JRE_HOME) {
    $javaExe = Join-Path (Split-Path -Parent $javac.Source) "java.exe"
    $r = Invoke-Native $javaExe @("-XshowSettings:properties", "-version")
    $homeLine = $r.Output | Where-Object { $_ -match '^\s*java\.home\s*=' } | Select-Object -First 1
    if ($homeLine) {
        $env:JAVA_HOME = ($homeLine -split '=', 2)[1].Trim()
    } else {
        $env:JAVA_HOME = Split-Path -Parent (Split-Path -Parent $javac.Source)
    }
}
Write-Host "    Java:   $(if ($env:JAVA_HOME) { $env:JAVA_HOME } else { $env:JRE_HOME })"

# --- 4. compile ----------------------------------------------------------------------
Step "Compiling"
$classes = Join-Path $root "build\classes"
if (Test-Path $classes) { Remove-Item -Recurse -Force $classes }
New-Item -ItemType Directory -Force $classes | Out-Null

$sources = Get-ChildItem -Recurse (Join-Path $root "src\main\java") -Filter *.java |
           Where-Object { $_.FullName -notmatch '\\com\\hms\\test\\' } |
           ForEach-Object { $_.FullName }
$argFile = Join-Path $env:TEMP "careconnect-sources.txt"
$sources | ForEach-Object { '"' + ($_ -replace '\\', '/') + '"' } | Set-Content -Encoding ASCII $argFile

Write-Host "    $($sources.Count) source files"
& javac -encoding UTF-8 -d $classes -cp "src\main\webapp\WEB-INF\lib\*" "@$argFile"
if ($LASTEXITCODE -ne 0) { Fail "Compilation failed (see errors above)." }

# --- 5. deploy -------------------------------------------------------------------------
Step "Deploying"
$app = Join-Path $TomcatHome "webapps\$ContextName"
Write-Host "    $app"
# The servlet API jar is compile-only; Tomcat provides its own at runtime.
robocopy "src\main\webapp" $app /E /XF jakarta.servlet-api-6.0.0.jar /XD classes /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { Fail "Copying web files failed (robocopy exit code $LASTEXITCODE)." }
robocopy $classes (Join-Path $app "WEB-INF\classes") /E /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { Fail "Copying classes failed (robocopy exit code $LASTEXITCODE)." }

$url = "http://localhost:8080/$ContextName/"
if ($NoStart) {
    Write-Host "Deployed. A running Tomcat reloads it within a few seconds: $url" -ForegroundColor Green
    exit 0
}

# --- 6. start ----------------------------------------------------------------------------
# Refuse to start a second Tomcat if port 8080 is taken (e.g. by the VS Code connector).
$inUse = $false
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $ar = $tcp.BeginConnect("127.0.0.1", 8080, $null, $null)
    $inUse = $ar.AsyncWaitHandle.WaitOne(500) -and $tcp.Connected
    $tcp.Close()
} catch { $inUse = $false }
if ($inUse) {
    Fail ("Port 8080 is already in use - another Tomcat is probably running (for example from the " +
          "VS Code Servers panel). Stop it and run again, or use  run.bat -NoStart  to redeploy into it.")
}

Write-Host ""
Write-Host "Starting Tomcat; the AI service starts with it." -ForegroundColor Green
Write-Host "Open $url   (Ctrl+C stops everything)" -ForegroundColor Green
Write-Host ""
$env:CATALINA_HOME = $TomcatHome
& (Join-Path $TomcatHome "bin\catalina.bat") run
