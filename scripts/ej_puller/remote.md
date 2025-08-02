I'll help you configure SSH for the remote device `27.147.158.194` and add it to your devices configuration. Let me break this down into steps:

## Step 1: SSH Configuration for Remote Device (27.147.158.194)

First, let's understand what needs to be done on the remote device to enable SSH log collection:

### On the Remote Device (27.147.158.194):

1. **Install and Enable OpenSSH Server** (if it's a Windows device):
```powershell
# Run as Administrator
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'
```

2. **Configure Windows Firewall**:
```powershell
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
```

3. **Create SSH user and set up authentication**:
   - Option A: **Password Authentication** (simpler but less secure)
   - Option B: **SSH Key Authentication** (recommended for security)

### For SSH Key Authentication (Recommended):

1. **On your collector machine**, generate an SSH key pair:
```bash
ssh-keygen -t ed25519 -C "log-collector@yourcompany.com" -f ~/.ssh/id_ed25519_logcollector
```
C:\Users\Administrator.NW-IMS-S2\.ssh
administrator@NW-IMS-S2
Administrator@27.147.158.194

2. **Copy the public key to the remote device**:
```bash
# Replace 'username' with actual username on remote device
ssh-copy-id -i ~/.ssh/id_ed25519_logcollector.pub username@27.147.158.194
```

Or manually copy the public key content to `%USERPROFILE%\.ssh\authorized_keys` on the remote device.

3. **Set proper permissions on remote device**:
```cmd
icacls %USERPROFILE%\.ssh /inheritance:r /grant:r "%USERNAME%:(OI)(CI)F"
icacls %USERPROFILE%\.ssh\authorized_keys /inheritance:r /grant:r "%USERNAME%:F"
```

## Step 2: Add Device Configuration to devices_advanced.json

Now let me add the new device configuration to your JSON file: 
```


Made changes.


```
## Configuration Details for the New Device

The configuration I added includes:

- **host**: `27.147.158.194` - Your remote device IP
- **username**: `loguser` - You'll need to replace this with the actual username on the remote device
- **key_filename**: Path to your private SSH key (update this path to match your system)
- **remote_log_path**: `C:/logs/application.log` - Update this to the actual log file path you want to collect
- **local_save_dir**: Local directory where logs will be saved
- **port**: 22 (standard SSH port)
- **timeout**: 15 seconds (slightly higher for remote connections)

## Step 3: Customize the Configuration

You'll need to update these values based on your specific setup:

1. **Replace `loguser`** with the actual username on the remote device
2. **Update the key path** to match where you store your SSH private key
3. **Update `remote_log_path`** to point to the actual log file(s) you want to collect
4. **Adjust the port** if SSH is running on a different port

Here are some common Windows log file locations you might want to collect:

```json
# Examples of common Windows log paths:
"remote_log_path": [
    "C:/Windows/System32/LogFiles/HttpErr/httperr1.log",
    "C:/inetpub/logs/LogFiles/W3SVC1/ex*.log",
    "C:/logs/application.log",
    "C:/ProgramData/YourApp/logs/app.log"
]
```

## Step 4: Test the Configuration

Once you've set up SSH on the remote device and updated the configuration, test it: 