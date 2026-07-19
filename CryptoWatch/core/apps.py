from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """Start the background price engine.

        Django's development server with autoreload can call `ready()` multiple times.
        We guard startup with an environment flag so we only start once per process.
        """
        import os

        if os.environ.get('CRYPTOWATCH_ENGINE_STARTED') == '1':
            return

        from .price_engine import PriceEngine

        try:
            os.environ['CRYPTOWATCH_ENGINE_STARTED'] = '1'
            engine = PriceEngine()
            engine.start()
        except Exception as exc:
            # Don't crash Django on engine startup issues.
            # In real apps, you'd log to a logger.
            print(f'[CryptoWatch] Failed to start PriceEngine: {exc}')


