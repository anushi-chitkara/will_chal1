from crontab import CronTab

def schedule_backup(interval):
    cron = CronTab(user=True)
    job = cron.new(command=f"python3 {os.path.abspath(__file__)} --backup")
    job.setall(interval)  # e.g., '0 2 * * *' for daily at 2 AM
    cron.write()

