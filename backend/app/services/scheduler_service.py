from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import datetime
from app.core.config import settings
from app.services.discovery_service import discovery_service

class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)
        self.is_running = False

    def scheduled_discovery_job(self):
        print(f"[{datetime.datetime.now()}] Running scheduled job discovery...")
        try:
            discovered = discovery_service.run_discovery()
            print(f"Discovered {len(discovered)} active opportunities.")
        except Exception as e:
            print(f"Error during scheduled discovery: {e}")

    def daily_report_job(self):
        print(f"[{datetime.datetime.now()}] Generating daily 9:00 AM summary report...")

    def start(self):
        if not self.is_running:
            # 1. Periodic discovery every N hours
            self.scheduler.add_job(
                self.scheduled_discovery_job,
                trigger=IntervalTrigger(hours=settings.JOB_SEARCH_INTERVAL_HOURS),
                id="job_discovery_worker",
                replace_existing=True
            )
            # 2. Daily report at 9:00 AM IST
            self.scheduler.add_job(
                self.daily_report_job,
                trigger=CronTrigger(hour=9, minute=0),
                id="daily_summary_worker",
                replace_existing=True
            )
            self.scheduler.start()
            self.is_running = True
            print("APScheduler workers started successfully.")

    def stop(self):
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False

    def trigger_discovery_now(self):
        self.scheduled_discovery_job()

scheduler_service = SchedulerService()
