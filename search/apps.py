from django.apps import AppConfig
from . import tracing  # tracing 설정 임포트
from .tasks import transfer_products_to_history  # tasks.py에서 작업 임포트
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
import time

logger = logging.getLogger(__name__)

class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'search'

    def ready(self):
        # OpenTelemetry 추적 설정 초기화
        try:
            tracing.setup_tracing()
        except Exception as e:
            logger.error("Failed to initialize OpenTelemetry tracing: %s", e)

        # 잠시 대기
        time.sleep(3)  # 필요한 경우 대기 시간 조정

        # 스케줄러 설정 및 시작
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            transfer_products_to_history,
            trigger=IntervalTrigger(seconds=10),
            id='transfer_products_to_history',
            replace_existing=True
        )
        scheduler.start()

 
