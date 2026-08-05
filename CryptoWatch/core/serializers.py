from __future__ import annotations

from rest_framework import serializers


class PortfolioTotalsSerializer(serializers.Serializer):
    total_cost = serializers.FloatField()
    total_value = serializers.FloatField()
    pnl_abs = serializers.FloatField()
    pnl_pct = serializers.FloatField()


class HoldingSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    quantity = serializers.FloatField()
    avg_buy_price = serializers.FloatField()
    current_price = serializers.FloatField()
    cost = serializers.FloatField()
    value = serializers.FloatField()
    pnl_abs = serializers.FloatField()
    pnl_pct = serializers.FloatField()


class PortfolioStateSerializer(serializers.Serializer):
    holdings = HoldingSerializer(many=True)
    totals = PortfolioTotalsSerializer()
    price_history = serializers.ListField(child=serializers.DictField())
    coin_histories = serializers.DictField(child=serializers.ListField(child=serializers.DictField()), required=False)
    transactions = serializers.ListField(child=serializers.DictField(), required=False)


class TradeRequestSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    action = serializers.ChoiceField(choices=['BUY', 'SELL', 'SOLD', 'buy', 'sell', 'sold'])
    quantity = serializers.FloatField()
    price = serializers.FloatField(required=False, default=0.0)


class AlertSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    target_price = serializers.FloatField()
    alert_type = serializers.ChoiceField(choices=['above', 'below', 'increase', 'decrease'])
    is_triggered = serializers.BooleanField()
    created_at = serializers.CharField(allow_null=True)
    triggered_at = serializers.CharField(allow_null=True)


class AlertCreateRequestSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    target_price = serializers.FloatField()
    alert_type = serializers.ChoiceField(choices=['above', 'below', 'increase', 'decrease'])

