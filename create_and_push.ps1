<#
.SYNOPSIS
Create FastAPI project skeleton files and push to remote branch `fastapi-skeleton`.

USAGE
1) If you're already inside your cloned repository root:
   - Open PowerShell (preferably as your normal user, not admin)
   - Allow script execution for this session:
       Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
   - Run:
       .\create_and_push.ps1

2) If you did NOT clone repository and want the script to init a git repo and push to a remote,
   pass RemoteUrl:
       .\create_and_push.ps1 -RemoteUrl "git@github.com:liuhuihui062-png/Mini-Game-Management-Platform.git"

NOTES
- Requires git in PATH and push access to the target remote.
- This script overwrites files with the same names in the current directory.
#>

param(
    [string]$RemoteUrl = ""
)

$ErrorActionPreference = "Stop"
$Branch = "fastapi-skeleton"

function Write-File {
    param($Path, $Content)
    $dir = Split-Path $Path -Parent
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $Content | Out-File -FilePath $Path -Encoding utf8 -Force
    Write-Host "Wrote $Path"
}

Write-Host "Starting create_and_push.ps1..."
Write-Host "Branch: $Branch"
if ($RemoteUrl -ne "") {
    Write-Host "RemoteUrl provided: $RemoteUrl"
}

# Create files
Write-Host "Creating project files..."

Write-File "README.md" @'
# Mini-Game-Management-Platform (FastAPI 骨架)

快速启动的 FastAPI 小游戏平台骨架，包含：
- 用户注册 / 登录（JWT）
- 游戏商店（列出游戏）
- 嵌入式游戏播放页（iframe + 手机容器）
- 已登录用户的游戏进度保存（server-side）与金币发放（简单防重放）

快速开始（本地开发）：
1. 创建虚拟环境并安装依赖：