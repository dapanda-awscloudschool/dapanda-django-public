""" #!/usr/bin/env python

import os
import sys
#from opentelemetry.instrumentation.django import DjangoInstrumentor

def main():
    #Run administrative tasks.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'final_project.settings')
    #아래만 추가
    #DjangoInstrumentor().instrument()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
 """
"""  #!/usr/bin/env python

import os
import sys
from opentelemetry.instrumentation.django import DjangoInstrumentor

def main():
    # Run administrative tasks.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'final_project.settings')

    # OpenTelemetry 초기화
    DjangoInstrumentor().instrument()

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
 """

""" #!/usr/bin/env python

import os
import sys
from opentelemetry.instrumentation.django import DjangoInstrumentor

def main():
    # Run administrative tasks.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'final_project.settings')

    # OpenTelemetry 초기화
    DjangoInstrumentor().instrument()

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
 """
#!/usr/bin/env python

import os
import sys
from opentelemetry.instrumentation.django import DjangoInstrumentor

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'final_project.settings')
    DjangoInstrumentor().instrument()
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()

