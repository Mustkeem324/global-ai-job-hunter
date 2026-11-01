from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import datetime
from typing import Dict, Any

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.schema import SourceHealth, SourceSyncCursor, ScheduledRun
from app.services.discovery_service import discovery_service

class SchedulerService:
    """
    Phase 4 Module 3: Autonomous Global Job Search Scheduler & Source Health Monitor
    Orchestrates high-priority discovery (3h), general sweeps (6h), and daily/weekly digests.
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)
        self.is_running = False

    def update_source_health(self, source_name: str, success: bool, latency_ms: float = 250.0):
        db = SessionLocal()
        try:
            sh = db.query(SourceHealth).filter(SourceHealth.source_name == source_name).first()
            if not sh:
                sh = SourceHealth(
                    source_name=source_name,
                    status="HEALTHY" if success else "DEGRADED",
                    error_count=0 if success else 1,
                    circuit_breaker_open=False,
                    avg_latency_ms=latency_ms
                )
                db.add(sh)
            else:
                sh.last_sync_at = datetime.datetime.now(datetime.timezone.utc)
                if success:
                    sh.status = "HEALTHY"
                    sh.error_count = max(0, sh.error_count - 1)
                    sh.circuit_breaker_open = False
                else:
                    sh.error_count += 1
                    if sh.error_count >= 5:
                        sh.status = "RATE_LIMITED"
                        sh.circuit_breaker_open = True
                    else:
                        sh.status = "DEGRADED"
                sh.avg_latency_ms = (sh.avg_latency_ms * 0.8) + (latency_ms * 0.2)
            db.commit()
        finally:
            db.close()

    def scheduled_discovery_job(self, high_priority_only: bool = False):
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        task_label = "high_priority_discovery" if high_priority_only else "general_discovery"
        print(f"[{now_dt}] Running scheduled job discovery ({task_label})...")

        db = SessionLocal()
        run_record = ScheduledRun(
            task_name=task_label,
            status="RUNNING",
            started_at=now_dt
        )
        db.add(run_record)
        db.commit()

        try:
            discovered = discovery_service.run_discovery(persist=True)
            run_record.status = "SUCCESS"
            run_record.jobs_discovered = len(discovered)
            run_record.completed_at = datetime.datetime.now(datetime.timezone.utc)
            self.update_source_health("global_aggregator", success=True)
            db.commit()
            print(f"Discovered {len(discovered)} active opportunities during {task_label}.")
        except Exception as e:
            run_record.status = "FAILED"
            run_record.error_message = str(e)
            run_record.completed_at = datetime.datetime.now(datetime.timezone.utc)
            self.update_source_health("global_aggregator", success=False)
            db.commit()
            print(f"Error during scheduled discovery: {e}")
        finally:
            db.close()

    def daily_report_job(self):
        """Generates 9:00 AM IST daily summary."""
        print(f"[{datetime.datetime.now()}] Generating daily 9:00 AM summary report...")
        from app.services.telegram_service import telegram_service
        try:
            telegram_service.send_daily_digest()
        except Exception as e:
            print(f"Error sending daily digest: {e}")

    def weekly_report_job(self):
        """Generates Sunday 7:00 PM IST weekly report."""
        print(f"[{datetime.datetime.now()}] Generating weekly Sunday 7:00 PM report...")
        from app.services.telegram_service import telegram_service
        try:
            telegram_service.send_weekly_digest()
        except Exception as e:
            print(f"Error sending weekly digest: {e}")

    def start(self):
        if not self.is_running:
            # 1. High-priority discovery: every 3 hours
            self.scheduler.add_job(
                lambda: self.scheduled_discovery_job(high_priority_only=True),
                trigger=IntervalTrigger(hours=3),
                id="high_priority_discovery_worker",
                replace_existing=True
            )
            # 2. General discovery: every 6 hours
            self.scheduler.add_job(
                lambda: self.scheduled_discovery_job(high_priority_only=False),
                trigger=IntervalTrigger(hours=settings.JOB_SEARCH_INTERVAL_HOURS),
                id="job_discovery_worker",
                replace_existing=True
            )
            # 3. Daily report: 9:00 AM IST
            self.scheduler.add_job(
                self.daily_report_job,
                trigger=CronTrigger(hour=9, minute=0),
                id="daily_summary_worker",
                replace_existing=True
            )
            # 4. Weekly report: Sunday 7:00 PM (19:00) IST
            self.scheduler.add_job(
                self.weekly_report_job,
                trigger=CronTrigger(day_of_week="sun", hour=19, minute=0),
                id="weekly_summary_worker",
                replace_existing=True
            )
            self.scheduler.start()
            self.is_running = True
            print("APScheduler Phase 4 multi-cadence workers started successfully.")

    def stop(self):
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False

    def trigger_discovery_now(self):
        self.scheduled_discovery_job()

scheduler_service = SchedulerService()
