from rest_framework import serializers


class HoldingSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)
    quantity = serializers.FloatField(min_value=0.0)
    avg_buy_price = serializers.FloatField(min_value=0.0)
    current_price = serializers.FloatField(min_value=0.0)
    cost = serializers.FloatField()
    value = serializers.FloatField()
    pnl_abs = serializers.FloatField()
    pnl_pct = serializers.FloatField()


class PortfolioTotalsSerializer(serializers.Serializer):
    total_cost = serializers.FloatField()
    total_value = serializers.FloatField()
    pnl_abs = serializers.FloatField()
    pnl_pct = serializers.FloatField()


class PortfolioStateSerializer(serializers.Serializer):
    holdings = HoldingSerializer(many=True)
    totals = PortfolioTotalsSerializer()
    price_history = serializers.ListField(child=serializers.DictField())
    coin_histories = serializers.DictField(
        child=serializers.ListField(child=serializers.DictField()),
        required=False,
    )
    transactions = serializers.ListField(child=serializers.DictField(), required=False)


class TradeRequestSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)
    action = serializers.ChoiceField(choices=['BUY', 'SELL', 'SOLD', 'buy', 'sell', 'sold'])
    quantity = serializers.FloatField(min_value=0.000001)
    price = serializers.FloatField(required=False, default=0.0, min_value=0.0)

    def validate_symbol(self, value: str) -> str:
        return value.strip().upper()

    def validate_action(self, value: str) -> str:
        val = value.strip().upper()
        return 'SOLD' if val in ('SELL', 'SOLD') else 'BUY'


class AlertSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)
    target_price = serializers.FloatField(min_value=0.0)
    alert_type = serializers.ChoiceField(choices=['above', 'below', 'increase', 'decrease'])
    is_triggered = serializers.BooleanField(default=False)
    created_at = serializers.CharField(allow_null=True, required=False)
    triggered_at = serializers.CharField(allow_null=True, required=False)


class AlertCreateRequestSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)
    target_price = serializers.FloatField(min_value=0.000001)
    alert_type = serializers.ChoiceField(choices=['above', 'below', 'increase', 'decrease'])

    def validate_symbol(self, value: str) -> str:
        return value.strip().upper()


class AlertDeactivateRequestSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)

    def validate_symbol(self, value: str) -> str:
        return value.strip().upper()


class LivePricesSerializer(serializers.Serializer):
    prices = serializers.DictField(child=serializers.FloatField())
