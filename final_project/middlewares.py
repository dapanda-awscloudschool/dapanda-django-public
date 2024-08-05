import logging
from django.utils import timezone

logger = logging.getLogger('django')

class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_response(self, request, response):
        if response.status_code == 200:
            # 원하는 로그 메시지 형식을 정의
            log_message = f"[{timezone.now()}] {request.method} {request.path} with status {response.status_code}"
            # 로그 메시지와 함께 추가 정보를 extra로 전달
            logger.info(log_message, extra={
                'custom_message': log_message,
                'request_path': request.path,
                'timestamp': timezone.now().isoformat(),
                'body': request.body.decode('utf-8') if request.body else 'None'
            })
        return response