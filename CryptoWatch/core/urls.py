from django.urls import path

from .api import (
    AlertCreateAPIView,
    AlertDeactivateAPIView,
    AlertsAPIView,
    LivePricesAPIView,
    PortfolioStateAPIView,
    TradeAPIView,
)
from .views import alert_form_submit, dashboard

urlpatterns = [
    # Frontend Pages
    path('', dashboard, name='dashboard'),
    path('alerts/create/', alert_form_submit, name='alerts_create_form'),

    # REST API Endpoints
    path('api/portfolio/', PortfolioStateAPIView.as_view(), name='api_portfolio'),
    path('api/trade/', TradeAPIView.as_view(), name='api_trade'),
    path('api/alerts/', AlertsAPIView.as_view(), name='api_alerts'),
    path('api/alerts/create/', AlertCreateAPIView.as_view(), name='api_create_alert'),
    path('api/alerts/deactivate/', AlertDeactivateAPIView.as_view(), name='api_alerts_deactivate'),
    path('api/live-prices/', LivePricesAPIView.as_view(), name='api_live_prices'),
]
