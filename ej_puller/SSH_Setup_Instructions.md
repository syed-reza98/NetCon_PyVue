# SSH Setup Instructions for Log Collection System

*Comprehensive guide for setting up SSH key authentication between devices*

---

## 📋 Overview

This guide covers the complete setup process for SSH key authentication between a **collector machine** (local) and **remote devices** for automated log collection. Based on the implementation for device `27.147.158.194`.

### System Architecture:
- **Collector Machine**: Windows machine running the log collection script
- **Remote Devices**: Windows machines with OpenSSH Server hosting log files
- **Authentication**: SSH key-based authentication (recommended) or password authentication

---

## 🖥️ Part 1: Collector Machine Setup (Local Machine)

### Prerequisites:
- Windows 10/11 with PowerShell
- Python 3.x installed
- Git Bash or Windows Subsystem for Linux (optional)

### Step 1: Install Required Software

#### Install OpenSSH Client (if not already installed):
```powershell
# Run as Administrator
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

#### Verify SSH Installation:
```powershell
ssh -V
```

### Step 2: Generate SSH Key Pair

#### Generate a new ED25519 key pair (recommended):
```bash
# Replace with your actual email/identifier
ssh-keygen -t ed25519 -C "Administrator@27.147.158.194" -f ~/.ssh/id_ed25519_remote194
```

#### On Windows PowerShell:
```powershell
ssh-keygen -t ed25519 -C "Administrator@27.147.158.194" -f $HOME\.ssh\id_ed25519_remote194
```

#### Key Generation Process:
1. **Enter passphrase**: Press Enter for no passphrase (recommended for automation)
2. **Confirm passphrase**: Press Enter again
3. **Files created**:
   - Private key: `~/.ssh/id_ed25519_remote194`
   - Public key: `~/.ssh/id_ed25519_remote194.pub`

### Step 3: Display Your Public Key

```powershell
# Windows PowerShell
Get-Content $HOME\.ssh\id_ed25519_remote194.pub
```

```bash
# Git Bash / Linux
cat ~/.ssh/id_ed25519_remote194.pub
```

**Example output:**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGTZYZUJ0s6Jcb92uP0z67iwL5WCyLniwVtJPZLEYdEs Administrator@27.147.158.194
```

### Step 4: Install Python Dependencies

```powershell
# Install paramiko for SSH/SFTP operations
pip install paramiko
```

---

## 🎯 Part 2: Remote Device Setup (Target Machine)

### Prerequisites:
- Windows Server 2016+ or Windows 10/11
- Administrator access
- Network connectivity from collector machine

### Step 1: Install OpenSSH Server

#### Method 1: Via Settings (Windows 10/11):
1. Go to **Settings** > **Apps** > **Optional Features**
2. Click **Add a feature**
3. Find and install **OpenSSH Server**

#### Method 2: Via PowerShell (Run as Administrator):
```powershell
# Install OpenSSH Server
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# Start the service
Start-Service sshd

# Set to start automatically
Set-Service -Name sshd -StartupType 'Automatic'

# Verify service is running
Get-Service sshd
```

### Step 2: Configure Windows Firewall

```powershell
# Allow SSH through Windows Firewall
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22

# Verify firewall rule
Get-NetFirewallRule -Name sshd
```

### Step 3: Test SSH Service

From the collector machine, test basic SSH connectivity:
```powershell
# This should prompt for password
ssh Administrator@27.147.158.194
```

### Step 4: Set Up SSH Key Authentication

#### On the Remote Device, run as Administrator:

```powershell
# 1. Create .ssh directory for the user
$sshDir = "C:\Users\Administrator.NW-IMS-S2\.ssh"
mkdir $sshDir -ErrorAction SilentlyContinue

# 2. Create authorized_keys file with your public key
$publicKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGTZYZUJ0s6Jcb92uP0z67iwL5WCyLniwVtJPZLEYdEs Administrator@27.147.158.194"
$authorizedKeysFile = "$sshDir\authorized_keys"
Add-Content -Path $authorizedKeysFile -Value $publicKey

# 3. Set proper permissions on .ssh directory
icacls $sshDir /inheritance:r /grant:r "Administrator:(OI)(CI)F"

# 4. Set proper permissions on authorized_keys file  
icacls $authorizedKeysFile /inheritance:r /grant:r "Administrator:F"

# 5. Verify the setup
Write-Host "SSH Directory exists: $(Test-Path $sshDir)"
Write-Host "Authorized keys file exists: $(Test-Path $authorizedKeysFile)"
Write-Host "Public key content:"
Get-Content $authorizedKeysFile
```

### Alternative: Manual File Creation

If the PowerShell method doesn't work, manually create the files:

1. **Create directory**: `C:\Users\Administrator.NW-IMS-S2\.ssh\`
2. **Create file**: `C:\Users\Administrator.NW-IMS-S2\.ssh\authorized_keys`
3. **Add public key content** to the `authorized_keys` file
4. **Set permissions** using the `icacls` commands above

---

## 🧪 Part 3: Testing SSH Key Authentication

### Step 1: Test SSH Connection

From the collector machine:
```powershell
# Test SSH key authentication
ssh -i C:\Users\syedr\.ssh\id_ed25519_remote194 Administrator@27.147.158.194 "echo 'SSH Key Authentication Successful!'"
```

**Expected Result**: Should execute without asking for password

### Step 2: Test SFTP Connection

```powershell
# Test SFTP connection
sftp -i C:\Users\syedr\.ssh\id_ed25519_remote194 Administrator@27.147.158.194
```

Commands to test within SFTP:
```bash
sftp> pwd
sftp> ls
sftp> cd C:/EJBackup
sftp> ls
sftp> quit
```

---

## ⚙️ Part 4: Log Collector Configuration

### Step 1: Create Device Configuration

Create or update `devices_advanced.json`:

```json
[
    {
        "host": "27.147.158.194",
        "username": "Administrator",
        "key_filename": "C:/Users/syedr/.ssh/id_ed25519_remote194",
        "remote_log_path": [
            "C:/EJBackup/EJ*.067",
            "C:/EJBackup/EJEB*.392", 
            "C:/EJBackup/new.txt"
        ],
        "local_save_dir": "./collected_logs/device_27_147_158_194/",
        "port": 22,
        "timeout": 15
    }
]
```

### Step 2: Test Log Collection

```powershell
# Test with advanced configuration
python log_collector.py --config devices_advanced.json

# Test with specific device only
python log_collector.py --config test_password_config.json
```

---

## 🔧 Part 5: Troubleshooting

### Common Issues and Solutions:

#### 1. SSH Key Authentication Fails
**Symptoms**: Still asks for password
**Solutions**:
- Verify public key is correctly added to `authorized_keys`
- Check file permissions with `icacls`
- Ensure `.ssh` directory exists
- Verify key file paths in configuration

#### 2. SSH Service Not Running
**Symptoms**: Connection refused
**Solutions**:
```powershell
# Check service status
Get-Service sshd

# Start service if stopped
Start-Service sshd

# Check firewall rules
Get-NetFirewallRule -Name sshd
```

#### 3. Permission Issues
**Symptoms**: Authentication failures, access denied
**Solutions**:
```powershell
# Reset permissions on .ssh directory
icacls "C:\Users\Administrator.NW-IMS-S2\.ssh" /inheritance:r /grant:r "Administrator:(OI)(CI)F"

# Reset permissions on authorized_keys
icacls "C:\Users\Administrator.NW-IMS-S2\.ssh\authorized_keys" /inheritance:r /grant:r "Administrator:F"
```

#### 4. Network Connectivity Issues
**Symptoms**: Connection timeout
**Solutions**:
- Test network connectivity: `ping 27.147.158.194`
- Check firewall on both machines
- Verify SSH service is listening: `netstat -an | findstr :22`

#### 5. File Path Issues
**Symptoms**: Remote file not found
**Solutions**:
- Verify file paths exist on remote machine
- Check file permissions on remote files
- Use forward slashes in paths: `C:/EJBackup/file.txt`

---

## 📁 Part 6: File Structure Reference

### Collector Machine File Structure:
```
C:\GitHub Repo\NW\NetCon_PyVue\ej_puller\
├── log_collector.py                    # Main log collection script
├── devices_advanced.json               # Device configuration file
├── test_password_config.json          # Test configuration
├── log_collector_run.log              # Execution log
├── collected_logs/                     # Downloaded log files
│   └── device_27_147_158_194/         # Device-specific logs
└── C:\Users\syedr\.ssh\               # SSH keys directory
    ├── id_ed25519_remote194           # Private key
    └── id_ed25519_remote194.pub       # Public key
```

### Remote Device File Structure:
```
C:\Users\Administrator.NW-IMS-S2\
├── .ssh\
│   └── authorized_keys                # Contains public keys
├── C:\EJBackup\                       # Log files location
│   ├── EJ00187120240902.067
│   ├── EJEB103220241031.392
│   └── new.txt
```

---

## 🔒 Part 7: Security Best Practices

### SSH Key Security:
1. **Use ED25519 keys** (more secure than RSA)
2. **Protect private keys** - never share or commit to version control
3. **Use different keys** for different servers
4. **Regular key rotation** - generate new keys periodically

### Remote Device Security:
1. **Limit SSH access** to specific IP addresses if possible
2. **Disable password authentication** once key auth is working
3. **Use non-standard SSH ports** if security requirements demand
4. **Regular security updates** on both machines

### Network Security:
1. **Use VPN** for connections over public networks
2. **Monitor SSH logs** for unauthorized access attempts
3. **Implement fail2ban** or similar intrusion prevention

---

## 📊 Part 8: Automation and Scheduling

### Windows Task Scheduler Setup:

1. **Open Task Scheduler**
2. **Create Basic Task**
3. **Configure**:
   - **Program/script**: `C:\path\to\python.exe`
   - **Arguments**: `log_collector.py --config devices_advanced.json --cleanup 30`
   - **Start in**: `C:\GitHub Repo\NW\NetCon_PyVue\ej_puller`
4. **Set schedule** (daily, hourly, etc.)

### PowerShell Script for Automation:
```powershell
# automated_log_collection.ps1
cd "C:\GitHub Repo\NW\NetCon_PyVue\ej_puller"
python log_collector.py --config devices_advanced.json --cleanup 30
```

---

## ✅ Part 9: Verification Checklist

### Pre-Deployment Checklist:
- [ ] OpenSSH Server installed and running on remote device
- [ ] Windows Firewall configured to allow SSH
- [ ] SSH key pair generated on collector machine
- [ ] Public key deployed to remote device
- [ ] File permissions set correctly on remote device
- [ ] SSH key authentication tested successfully
- [ ] Log file paths verified and accessible
- [ ] Python dependencies installed
- [ ] Configuration file updated with correct paths
- [ ] Log collection tested manually
- [ ] Automation scheduled (if required)

### Post-Deployment Monitoring:
- [ ] Check log collection success rates
- [ ] Monitor disk space on collector machine
- [ ] Verify log file integrity
- [ ] Review security logs for unauthorized access
- [ ] Test backup and recovery procedures

---

## 📞 Support and Maintenance

### Log Files to Monitor:
- `log_collector_run.log` - Script execution logs
- Windows Event Logs - SSH service logs
- Application logs on remote devices

### Regular Maintenance Tasks:
1. **Clean up old collected logs** (use `--cleanup` option)
2. **Rotate SSH keys** annually
3. **Update Python dependencies** regularly
4. **Review and update device configurations**
5. **Test backup and recovery procedures**

---

*Created: June 26, 2025*  
*Based on implementation for device 27.147.158.194*  
*Log Collection System v1.0*
