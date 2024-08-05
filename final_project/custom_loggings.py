import logging
import json
from datetime import datetime

class CustomJSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'module': record.module,
            'message': record.getMessage(),
            'path': record.pathname,
            'line': record.lineno,
            'status_code': getattr(record, 'status_code', None),
            'request_path': getattr(record, 'request_path', None),
            'custom_message': getattr(record, 'custom_message', None),
            'body': getattr(record, 'body', None)
        }
        return json.dumps(log_record, ensure_ascii=False)

# logging 설정
logger = logging.getLogger('django')
handler = logging.StreamHandler()
formatter = CustomJSONFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)