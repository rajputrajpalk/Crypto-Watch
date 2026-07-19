from __future__ import annotations

from rest_framework import serializers


class LivePricesSerializer(serializers.Serializer):
    prices = serializers.DictField(child=serializers.FloatField())

