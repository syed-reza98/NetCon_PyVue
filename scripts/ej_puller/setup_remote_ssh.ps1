# SSH Key Setup Script for Remote Device 27.147.158.194
# Run this script to set up SSH key authentication

Write-Host "SSH Key Setup for Remote Device 27.147.158.194" -ForegroundColor Green
Write-Host "=" * 50

# Display the public key that needs to be copied
Write-Host "`nYour public key content:" -ForegroundColor Yellow
Get-Content "$env:USERPROFILE\.ssh\id_ed25519_remote194.pub"

Write-Host "`n" + "=" * 50
Write-Host "INSTRUCTIONS:" -ForegroundColor Cyan
Write-Host "1. Connect to the remote device 27.147.158.194"
Write-Host "2. Open PowerShell as Administrator"
Write-Host "3. Run these commands on the REMOTE device:"
Write-Host ""
Write-Host "   # Create .ssh directory if it doesn't exist" -ForegroundColor White
Write-Host "   mkdir C:\Users\Administrator.NW-IMS-S2\.ssh -ErrorAction SilentlyContinue" -ForegroundColor Gray
Write-Host ""
Write-Host "   # Create or append to authorized_keys file" -ForegroundColor White
Write-Host "   Add-Content -Path 'C:\Users\Administrator.NW-IMS-S2\.ssh\authorized_keys' -Value 'PASTE_PUBLIC_KEY_HERE'" -ForegroundColor Gray
Write-Host ""
Write-Host "   # Set proper permissions" -ForegroundColor White
Write-Host "   icacls C:\Users\Administrator.NW-IMS-S2\.ssh /inheritance:r /grant:r 'Administrator:(OI)(CI)F'" -ForegroundColor Gray
Write-Host "   icacls C:\Users\Administrator.NW-IMS-S2\.ssh\authorized_keys /inheritance:r /grant:r 'Administrator:F'" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Replace 'PASTE_PUBLIC_KEY_HERE' with the public key shown above"
Write-Host ""
Write-Host "5. Test the connection by running:" -ForegroundColor Green
Write-Host "   ssh -i $env:USERPROFILE\.ssh\id_ed25519_remote194 Administrator@27.147.158.194"
