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

def collect_log(device):
    try:
        os.makedirs(device['local_save_dir'], exist_ok=True)
        local_filename = os.path.join(
            device['local_save_dir'],
            f"{device['host']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_kwargs = {
            'hostname': device['host'],
            'username': device['username'],
            'timeout': device.get('timeout', 10)
        }
        if 'key_filename' in device:
            connect_kwargs['key_filename'] = device['key_filename']
        if 'password' in device:
            connect_kwargs['password'] = device['password']
        if 'port' in device:
            connect_kwargs['port'] = device['port']
        ssh.connect(**connect_kwargs)
        sftp = ssh.open_sftp()
        try:
            sftp.stat(device['remote_log_path'])  # Check if file exists
        except FileNotFoundError:
            logging.error(f"Remote file not found: {device['remote_log_path']} on {device['host']}")
            print(f"Remote file not found: {device['remote_log_path']} on {device['host']}")
            sftp.close()
            ssh.close()
            return
        # Support for multiple log files per device
        if isinstance(device['remote_log_path'], list):
            for remote_path in device['remote_log_path']:
                local_file = os.path.join(
                    device['local_save_dir'],
                    f"{device['host']}_{os.path.basename(remote_path)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                )
                try:
                    sftp.get(remote_path, local_file)
                    logging.info(f"Collected log from {device['host']}:{remote_path} to {local_file}")
                    print(f"Collected log from {device['host']}:{remote_path} to {local_file}")
                except Exception as e:
                    logging.error(f"Failed to collect {remote_path} from {device['host']}: {e}")
                    print(f"Failed to collect {remote_path} from {device['host']}: {e}")
        else:
            sftp.get(device['remote_log_path'], local_filename)
            logging.info(f"Collected log from {device['host']} to {local_filename}")
            print(f"Collected log from {device['host']} to {local_filename}")
        sftp.close()
        ssh.close()
    except Exception as e:
        logging.error(f"Failed to collect from {device.get('host', 'unknown')}: {e}")
        print(f"Failed to collect from {device.get('host', 'unknown')}: {e}")

def collect_logs_parallel(devices):
    threads = []
    for device in devices:
        t = threading.Thread(target=collect_log, args=(device,))
        t.start()
        threads.append(t)
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
