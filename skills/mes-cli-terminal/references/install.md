# Installation Guide for AI Agents & Users

This guide provides instructions for installing and configuring `mes-cli` in Linux, macOS, and Windows environments using the public Aliyun OSS mirror.

## 1. Latest Version Information

The latest version metadata can be retrieved from:
`https://oss-emcsprod-public.oss-cn-beijing.aliyuncs.com/tools/mes/version.json`

## 2. Installation (Linux)

Suitable for AI agents, servers, and WSL environments.

### Automated Script (Bash)

```bash
# 1. Fetch latest version
OSS_BASE="https://oss-emcsprod-public.oss-cn-beijing.aliyuncs.com/tools/mes"
VERSION=$(curl -s "${OSS_BASE}/version.json" | sed -n 's/.*"version": *"\([^"]*\)".*/\1/p')

# 2. Download Linux amd64 zip
URL="${OSS_BASE}/${VERSION}/mes-${VERSION}-linux-amd64.zip"
curl -L -o mes-cli.zip "${URL}"

# 3. Unzip and install
mkdir -p ~/.mes/bin
unzip mes-cli.zip -d mes-cli-tmp
mv mes-cli-tmp/bin/mes ~/.mes/bin/
rm -rf mes-cli.zip mes-cli-tmp

# 4. Add to PATH (add to ~/.bashrc or ~/.zshrc if not present)
export PATH="$HOME/.mes/bin:$PATH"

# 5. Verify
mes version
```

# 3. Installation (macOS)

### Automated Script (Bash/Zsh)

```bash
# 1. Fetch latest version
OSS_BASE="https://oss-emcsprod-public.oss-cn-beijing.aliyuncs.com/tools/mes"
VERSION=$(curl -s "${OSS_BASE}/version.json" | sed -n 's/.*"version": *"\([^"]*\)".*/\1/p')

# 2. Identify architecture (amd64 or arm64)
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then PKG_ARCH="amd64"; else PKG_ARCH="arm64"; fi

# 3. Download macOS zip
URL="${OSS_BASE}/${VERSION}/mes-${VERSION}-macOS-${PKG_ARCH}.zip"
curl -L -o mes-cli.zip "${URL}"

# 4. Unzip and install
mkdir -p ~/.mes/bin
unzip mes-cli.zip -d mes-cli-tmp
mv mes-cli-tmp/bin/mes ~/.mes/bin/
rm -rf mes-cli.zip mes-cli-tmp

# 5. Add to PATH (add to ~/.zshrc or ~/.bash_profile if not present)
export PATH="$HOME/.mes/bin:$PATH"

# 6. Verify
mes version
```

# 4. Installation (Windows)

Suitable for developers and agents running natively on Windows.

### Automated Script (PowerShell)

```powershell
# 1. Fetch latest version
$OSS_BASE = "https://oss-emcsprod-public.oss-cn-beijing.aliyuncs.com/tools/mes"
$versionJson = Invoke-RestMethod -Uri "${OSS_BASE}/version.json"
$VERSION = $versionJson.version

# 2. Download Windows amd64 zip
$URL = "${OSS_BASE}/${VERSION}/mes-${VERSION}-windows-amd64.zip"
Invoke-WebRequest -Uri $URL -OutFile "mes-cli.zip"

# 3. Unzip
Expand-Archive -Path "mes-cli.zip" -DestinationPath "mes-cli-tmp" -Force

# 4. Install to ~/.mes/bin and add to PATH
$targetDir = Join-Path $HOME ".mes\bin"
if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force }
Move-Item -Path "mes-cli-tmp\bin\mes.exe" -Destination (Join-Path $targetDir "mes.exe") -Force

# Add to User PATH if not already present
$path = [Environment]::GetEnvironmentVariable("Path", "User")
if ($path -notlike "*$targetDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$path;$targetDir", "User")
    $env:Path = "$env:Path;$targetDir"
}

# 5. Cleanup
Remove-Item -Recurse -Force mes-cli.zip, mes-cli-tmp

# 6. Verify
mes version
```

## 5. Configuration for AI Agents

- **Non-Interactive**: Always use `-o json` and explicitly pass all flags.
- **Session**: Auth info is stored in `~/.mes/config.yaml` (Linux/WSL) or `%USERPROFILE%\.mes\config.yaml` (Windows).
- **Encoding**: For Windows → WSL calls, see `SKILL.md` for encoding-safe procedures.
