# Log Collector using SSH/SFTP
# Author: GitHub Copilot
# Description: Collects log files from remote Windows devices using SSH/SFTP (OpenSSH)

import paramiko
import os
from datetime import datetime
import threading
import logging
import json
import argparse
import fnmatch

# Setup logging
LOG_FILE = 'log_collector_run.log'
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# List of remote devices and log file paths
REMOTE_DEVICES = [
    # Demo public SFTP server (Rebex)
    {
        'host': 'test.rebex.net',
        'username': 'demo',
        'password': 'password',  # Using password authentication for the demo
        'remote_log_path': '/readme.txt',  # Publicly available file on the server
        'local_save_dir': './collected_logs/'
    },
]

def load_devices_from_json(json_path):
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load device config: {e}")
        return []

def get_matching_files(sftp, pattern):
    """Get list of files matching a glob pattern on remote server."""
    try:
        # Extract directory and pattern
        directory = os.path.dirname(pattern) or '.'
        file_pattern = os.path.basename(pattern)
        
        # List files in the directory
        files = sftp.listdir(directory)
        
        # Filter files matching the pattern
        matching_files = []
        for file in files:
            if fnmatch.fnmatch(file, file_pattern):
                full_path = f"{directory}/{file}".replace('\\', '/')
                matching_files.append(full_path)
        
        return matching_files
    except Exception as e:
        logging.error(f"Error listing files for pattern {pattern}: {e}")
        return []

def collect_log(device):
    try:
        os.makedirs(device['local_save_dir'], exist_ok=True)
        local_filename = os.path.join(
            device['local_save_dir'],
            f"{device['host']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Configure connection parameters with better defaults
        connect_kwargs = {
            'hostname': device['host'],
            'username': device['username'],
            'timeout': device.get('timeout', 10),
            'banner_timeout': 30,  # Increase banner timeout
            'auth_timeout': 30,    # Increase auth timeout
            'allow_agent': False,  # Disable SSH agent to avoid conflicts
            'look_for_keys': False  # Disable automatic key discovery
        }
        
        if 'key_filename' in device:
            connect_kwargs['key_filename'] = device['key_filename']
            connect_kwargs['look_for_keys'] = True  # Enable key lookup only when specified
        if 'password' in device:
            connect_kwargs['password'] = device['password']
        if 'port' in device:
            connect_kwargs['port'] = device['port']
            
        ssh.connect(**connect_kwargs)
        sftp = ssh.open_sftp()
        
        # Support for multiple log files per device
        if isinstance(device['remote_log_path'], list):
            all_files_to_collect = []
            
            for remote_path in device['remote_log_path']:
                # Check if path contains wildcards
                if '*' in remote_path or '?' in remote_path:
                    # Handle wildcard patterns
                    matching_files = get_matching_files(sftp, remote_path)
                    if matching_files:
                        all_files_to_collect.extend(matching_files)
                        logging.info(f"Found {len(matching_files)} files matching pattern {remote_path} on {device['host']}")
                    else:
                        logging.warning(f"No files found matching pattern {remote_path} on {device['host']}")
                else:
                    # Handle exact file paths
                    try:
                        sftp.stat(remote_path)  # Check if file exists
                        all_files_to_collect.append(remote_path)
                    except FileNotFoundError:
                        logging.error(f"Remote file not found: {remote_path} on {device['host']}")
                        print(f"Remote file not found: {remote_path} on {device['host']}")
            
            # Collect all found files
            for remote_file in all_files_to_collect:
                local_file = os.path.join(
                    device['local_save_dir'],
                    f"{device['host']}_{os.path.basename(remote_file)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                )
                try:
                    sftp.get(remote_file, local_file)
                    logging.info(f"Collected log from {device['host']}:{remote_file} to {local_file}")
                    print(f"Collected log from {device['host']}:{remote_file} to {local_file}")
                except Exception as e:
                    logging.error(f"Failed to collect {remote_file} from {device['host']}: {e}")
                    print(f"Failed to collect {remote_file} from {device['host']}: {e}")
        else:
            # Single file path
            remote_path = device['remote_log_path']
            if '*' in remote_path or '?' in remote_path:
                # Handle wildcard pattern
                matching_files = get_matching_files(sftp, remote_path)
                for remote_file in matching_files:
                    local_file = os.path.join(
                        device['local_save_dir'],
                        f"{device['host']}_{os.path.basename(remote_file)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                    )
                    try:
                        sftp.get(remote_file, local_file)
                        logging.info(f"Collected log from {device['host']}:{remote_file} to {local_file}")
                        print(f"Collected log from {device['host']}:{remote_file} to {local_file}")
                    except Exception as e:
                        logging.error(f"Failed to collect {remote_file} from {device['host']}: {e}")
                        print(f"Failed to collect {remote_file} from {device['host']}: {e}")
            else:
                # Exact file path
                try:
                    sftp.stat(remote_path)  # Check if file exists
                    sftp.get(remote_path, local_filename)
                    logging.info(f"Collected log from {device['host']} to {local_filename}")
                    print(f"Collected log from {device['host']} to {local_filename}")
                except FileNotFoundError:
                    logging.error(f"Remote file not found: {remote_path} on {device['host']}")
                    print(f"Remote file not found: {remote_path} on {device['host']}")
            
    except paramiko.AuthenticationException as e:
        logging.error(f"Authentication failed for {device.get('host', 'unknown')}: {e}")
        print(f"Authentication failed for {device.get('host', 'unknown')}: {e}")
    except paramiko.SSHException as e:
        logging.error(f"SSH connection error for {device.get('host', 'unknown')}: {e}")
        print(f"SSH connection error for {device.get('host', 'unknown')}: {e}")
    except Exception as e:
        logging.error(f"Failed to collect from {device.get('host', 'unknown')}: {e}")
        print(f"Failed to collect from {device.get('host', 'unknown')}: {e}")
    finally:
        # Ensure cleanup even if errors occur
        try:
            if 'sftp' in locals():
                sftp.close()
            if 'ssh' in locals():
                ssh.close()
        except Exception:
            pass  # Ignore cleanup errors

def collect_logs_parallel(devices):
    import time
    threads = []
    for i, device in enumerate(devices):
        t = threading.Thread(target=collect_log, args=(device,))
        t.start()
        threads.append(t)
        # Small delay between starting threads to prevent connection conflicts
        if i < len(devices) - 1:  # Don't delay after the last device
            time.sleep(0.5)
    for t in threads:
        t.join()

def cleanup_old_logs(log_dir, days=30):
    now = datetime.now().timestamp()
    for root, dirs, files in os.walk(log_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.isfile(file_path):
                mtime = os.path.getmtime(file_path)
                if (now - mtime) > days * 86400:
                    os.remove(file_path)
                    logging.info(f"Deleted old log file: {file_path}")

def main():
    parser = argparse.ArgumentParser(description='Collect logs from remote devices via SSH/SFTP.')
    parser.add_argument('--config', type=str, help='Path to JSON config file with device list.')
    parser.add_argument('--cleanup', type=int, default=0, help='Delete logs older than N days (0=disable).')
    args = parser.parse_args()

    if args.config:
        devices = load_devices_from_json(args.config)
    else:
        devices = REMOTE_DEVICES

    if not devices:
        print("No devices to collect from.")
        return

    collect_logs_parallel(devices)

    if args.cleanup > 0:
        for device in devices:
            cleanup_old_logs(device['local_save_dir'], days=args.cleanup)

if __name__ == "__main__":
    main()
