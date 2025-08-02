# SSH Key Setup Commands for Remote Device 27.147.158.194
# Run these commands on the REMOTE device as Administrator

Write-Host "Setting up SSH Key Authentication..." -ForegroundColor Green

# 1. Create .ssh directory if it doesn't exist
$sshDir = "C:\Users\Administrator.NW-IMS-S2\.ssh"
if (!(Test-Path $sshDir)) {
    mkdir $sshDir
    Write-Host "Created .ssh directory: $sshDir" -ForegroundColor Yellow
} else {
    Write-Host ".ssh directory already exists: $sshDir" -ForegroundColor Green
}

# 2. Your public key (this will be added to authorized_keys)
$publicKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGTZYZUJ0s6Jcb92uP0z67iwL5WCyLniwVtJPZLEYdEs Administrator@27.147.158.194"

# 3. Add public key to authorized_keys
$authorizedKeysFile = "$sshDir\authorized_keys"
Add-Content -Path $authorizedKeysFile -Value $publicKey
Write-Host "Added public key to: $authorizedKeysFile" -ForegroundColor Green

# 4. Set proper permissions on .ssh directory
icacls $sshDir /inheritance:r /grant:r "Administrator:(OI)(CI)F"
Write-Host "Set permissions on .ssh directory" -ForegroundColor Green

# 5. Set proper permissions on authorized_keys file
icacls $authorizedKeysFile /inheritance:r /grant:r "Administrator:F"
Write-Host "Set permissions on authorized_keys file" -ForegroundColor Green

# 6. Verify the setup
Write-Host "`nVerification:" -ForegroundColor Cyan
Write-Host "SSH Directory: $(Test-Path $sshDir)" -ForegroundColor White
Write-Host "Authorized Keys File: $(Test-Path $authorizedKeysFile)" -ForegroundColor White
Write-Host "Public Key Content:" -ForegroundColor White
Get-Content $authorizedKeysFile

Write-Host "`nSSH Key setup completed successfully!" -ForegroundColor Green
Write-Host "You can now test passwordless SSH from your local machine." -ForegroundColor Yellow
