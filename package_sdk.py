import os
import shutil
import zipfile

def create_sdk():
    print("=========================================")
    print("      NovaLang Windows SDK Packager      ")
    print("=========================================")
    
    sdk_name = "nova-sdk-windows"
    temp_dir = sdk_name
    
    # 1. Clean previous temp files
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        
    os.makedirs(temp_dir)
    os.makedirs(f"{temp_dir}/bin")
    
    # 2. Copy Executable
    exe_src = "dist/nova.exe"
    if not os.path.exists(exe_src):
        print(f"Error: Compiled binary '{exe_src}' not found. Please run 'build_release.py' first.")
        return
        
    shutil.copy2(exe_src, f"{temp_dir}/bin/nova.exe")
    print("Copied binary executable...")
    
    # 3. Copy Standard Libraries
    shutil.copytree("novalang/stdlib", f"{temp_dir}/stdlib")
    print("Copied standard libraries...")
    
    # 4. Copy Editor Configurations
    shutil.copytree("editors", f"{temp_dir}/editors")
    print("Copied editor configurations...")
    
    # 5. Create PowerShell Installer Script (install.ps1)
    installer_content = """# PowerShell Installer for NovaLang Windows SDK
$sdkDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$installDest = "$env:USERPROFILE\\.nova"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "     Installing NovaLang Windows SDK     " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Create directory structures
Write-Host "[1/4] Copying SDK files to $installDest..." -ForegroundColor Yellow
if (Test-Path $installDest) {
    Remove-Item -Recurse -Force $installDest
}
New-Item -ItemType Directory -Force -Path "$installDest\\bin" | Out-Null

# Copy files
Copy-Item -Path "$sdkDir\\bin\\nova.exe" -Destination "$installDest\\bin\\nova.exe"
Copy-Item -Recurse -Path "$sdkDir\\stdlib" -Destination "$installDest\\stdlib"
Copy-Item -Recurse -Path "$sdkDir\\editors" -Destination "$installDest\\editors"

# 2. Update Environment PATH
Write-Host "[2/4] Adding $installDest\\bin to User PATH..." -ForegroundColor Yellow
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$installDest\\bin*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$installDest\\bin", "User")
    $env:Path = "$env:Path;$installDest\\bin"
    Write-Host "Added to User PATH." -ForegroundColor Green
} else {
    Write-Host "PATH already registered." -ForegroundColor Green
}

# 3. Check / Install LLVM Clang dependency
Write-Host "[3/4] Checking for LLVM Clang compiler dependency..." -ForegroundColor Yellow
$clangPath = Get-Command clang -ErrorAction SilentlyContinue
if (-not $clangPath) {
    Write-Host "LLVM Clang compiler not found. Clang is required for native builds (nova build)." -ForegroundColor Yellow
    $choice = Read-Host "Would you like to install LLVM Clang automatically using winget? (Y/N)"
    if ($choice -eq "Y" -or $choice -eq "y") {
        Write-Host "Installing LLVM Clang via winget... This may take a moment." -ForegroundColor Yellow
        winget install --id LLVM.LLVM --silent --accept-source-agreements --accept-package-agreements
        if ($LASTEXITCODE -eq 0) {
            Write-Host "LLVM Clang installed successfully! Please restart all terminal windows to refresh your PATH." -ForegroundColor Green
        } else {
            Write-Host "winget installation returned code $LASTEXITCODE. You may need to install LLVM manually from: https://github.com/llvm/llvm-project/releases" -ForegroundColor Red
        }
    } else {
        Write-Host "Skipped LLVM installation. You must install Clang manually to run native compilations." -ForegroundColor Cyan
    }
} else {
    Write-Host "LLVM Clang detected at $($clangPath.Source)" -ForegroundColor Green
}

# 4. Complete
Write-Host "[4/4] Installation Complete!" -ForegroundColor Green
Write-Host "Please restart your terminal window." -ForegroundColor Yellow
Write-Host "Test the installation using: nova repl" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
"""
    with open(f"{temp_dir}/install.ps1", "w", encoding="utf-8") as f:
        f.write(installer_content)
    print("Created PowerShell installer script...")
    
    # 6. Create SDK README
    readme_content = """# NovaLang SDK for Windows

Welcome to the NovaLang Software Development Kit (SDK) for Windows!

## Contents
* `bin/nova.exe` - Standalone compiled compiler, VM runtime, and REPL manager.
* `stdlib/` - Reference code files for standard library modules.
* `editors/` - Syntax definitions and configuration packages for IDEs (e.g. VS Code).
* `install.ps1` - PowerShell installation automation script.

## Setup Instructions

1. Open PowerShell as an administrator or user.
2. Navigate to the extracted SDK folder.
3. Run the installer script:
   ```powershell
   .\\install.ps1
   ```
4. Restart your terminal window to reload the PATH variable.
5. Verify the installation:
   ```cmd
   nova repl
   ```

Happy coding with NovaLang!
"""
    with open(f"{temp_dir}/README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("Created SDK README.md...")
    
    # 7. Zip the directory
    zip_dest = "dist/nova-sdk-windows.zip"
    if os.path.exists(zip_dest):
        os.remove(zip_dest)
        
    print("\nZipping files...")
    with zipfile.ZipFile(zip_dest, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=os.path.dirname(temp_dir))
                zipf.write(file_path, arcname)
                
    print(f"Windows SDK zipped successfully!")
    print(f"Output Path: {zip_dest}")
    
    # 8. Clean up temp folder
    shutil.rmtree(temp_dir)
    print("Cleaned up temporary workspace.")
    print("=========================================")

if __name__ == "__main__":
    create_sdk()
