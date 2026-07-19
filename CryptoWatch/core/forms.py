from __future__ import annotations

import re
from typing import Dict

from django import forms


COIN_SYMBOL_RE = re.compile(r"^[A-Z]{3,5}$")


ALERT_TYPE_CHOICES = [
    ("above", "Above Target Price"),
    ("below", "Below Target Price / Stop-Loss"),
]


class AlertConfigForm(forms.Form):
    """User-facing alert configuration form with strict sanitization."""

    coin_symbol = forms.CharField(
        label="coin_symbol",
        max_length=10,
        required=True,
        strip=True,
        help_text="e.g. BTC, ETH",
    )
    target_price = forms.FloatField(label="target_price", required=True, min_value=0.0)
    alert_type = forms.ChoiceField(choices=ALERT_TYPE_CHOICES, required=True)

    def clean_coin_symbol(self) -> str:
        raw = (self.cleaned_data.get("coin_symbol") or "").strip().upper()
        if not raw:
            raise forms.ValidationError("coin_symbol is required")
        if not COIN_SYMBOL_RE.match(raw):
            raise forms.ValidationError("Invalid coin symbol. Must match ^[A-Z]{3,5}$")
        return raw

    def clean_target_price(self) -> float:
        raw = self.cleaned_data.get("target_price")
        try:
            val = float(raw)
        except (TypeError, ValueError):
            raise forms.ValidationError("target_price must be a positive number")
        if val <= 0:
            raise forms.ValidationError("target_price must be greater than zero")
        return val

    def to_payload(self) -> Dict[str, object]:
        """Convert to existing API/repository payload schema."""
        return {
            "symbol": self.cleaned_data["coin_symbol"],
            "target_price": self.cleaned_data["target_price"],
            "alert_type": self.cleaned_data["alert_type"],
        }

