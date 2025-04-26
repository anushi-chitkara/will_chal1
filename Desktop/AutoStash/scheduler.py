#!/usr/bin/env python3
import os
import sys
import subprocess

def setup_schedule(cron_schedule, script_path):
    """Set up a scheduled backup using either cron or systemd"""
    # First try systemd (more modern)
    try:
        setup_systemd(script_path)
        return "Scheduled with systemd"
    except Exception as e:
        # Fall back to cron
        try:
            setup_cron(cron_schedule, script_path)
            return "Scheduled with cron"
        except Exception as e:
            raise Exception(f"Failed to set up schedule: {str(e)}")

def setup_systemd(script_path):
    """Set up backup with systemd timer (modern Linux systems)"""
    # Create service file
    service_content = f"""[Unit]
Description=AutoStash Backup Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 {script_path}
User={os.getenv('USER')}

[Install]
WantedBy=multi-user.target
"""

    # Create timer file
    timer_content = """[Unit]
Description=Run AutoStash backup daily

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""

    # Write service file
    service_path = os.path.expanduser("~/.config/systemd/user/autostash.service")
    os.makedirs(os.path.dirname(service_path), exist_ok=True)
    with open(service_path, "w") as f:
        f.write(service_content)

    # Write timer file
    timer_path = os.path.expanduser("~/.config/systemd/user/autostash.timer")
    with open(timer_path, "w") as f:
        f.write(timer_content)

    # Enable and start the timer
    subprocess.run(["systemctl", "--user", "enable", "autostash.timer"])
    subprocess.run(["systemctl", "--user", "start", "autostash.timer"])

def setup_cron(cron_schedule, script_path):
    """Set up backup with cron (works on all Linux systems)"""
    from crontab import CronTab
    
    # Get current user's crontab
    cron = CronTab(user=True)
    
    # Remove any existing AutoStash jobs
    for job in cron.find_comment('AutoStash Backup'):
        cron.remove(job)
    
    # Create new job
    job = cron.new(command=f'/usr/bin/python3 {script_path}')
    job.setall(cron_schedule)
    job.set_comment('AutoStash Backup')
    
    # Write to crontab
    cron.write()

# If run directly (by scheduler)
if __name__ == "__main__":
    # This allows the script to be called by cron/systemd
    # It will perform backup with default options
    from backup_logic import BackupManager
    from config_manager import ConfigManager
    import keyring
    
    # Load configuration
    config = ConfigManager()
    folders = config.get_folders()
    
    # Get GitHub token
    token = keyring.get_password("autostash", "github_token")
    if not token:
        sys.exit("No GitHub token found")
    
    # Run backup
    backup = BackupManager()
    try:
        backup.run(folders, "default_repo")
    except Exception as e:
        # Log error
        with open(os.path.expanduser("~/.autostash/error.log"), "a") as f:
            f.write(f"{datetime.datetime.now()}: {str(e)}\n")
        sys.exit(1)


