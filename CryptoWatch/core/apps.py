import os
import sys
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'CryptoWatch Core'

    def ready(self):
        """Initialize the background price tracking engine when the server starts."""
        # Avoid running engine during migrations, tests, or management commands
        cmd = sys.argv[1] if len(sys.argv) > 1 else ''
        if cmd in ('makemigrations', 'migrate', 'collectstatic', 'check'):
            return

        # Guard against Django's auto-reloader double execution
        if os.environ.get('CRYPTOWATCH_ENGINE_INITIALIZED') == '1':
            return

        try:
            from .price_engine import PriceEngine
            os.environ['CRYPTOWATCH_ENGINE_INITIALIZED'] = '1'
            engine = PriceEngine()
            engine.start()
        except Exception as exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to start PriceEngine on app ready: %s", exc)
