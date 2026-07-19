from django.urls import path

from .api import AlertCreateAPIView, AlertsAPIView, PortfolioStateAPIView
from .api_live_prices import LivePricesAPIView
from .api_alerts_deactivate import AlertDeactivateAPIView
from .views import alert_form_submit, dashboard

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('alerts/create/', alert_form_submit, name='alerts_create'),
    path('api/portfolio/', PortfolioStateAPIView.as_view(), name='api_portfolio'),
    path('api/alerts/', AlertsAPIView.as_view(), name='api_alerts'),
    path('api/alerts/create/', AlertCreateAPIView.as_view(), name='api_create_alert'),
    path('api/alerts/deactivate/', AlertDeactivateAPIView.as_view(), name='api_alerts_deactivate'),
    path('api/live-prices/', LivePricesAPIView.as_view(), name='api_live_prices'),
]











