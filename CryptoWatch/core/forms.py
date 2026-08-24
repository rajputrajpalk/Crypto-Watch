from django import forms
from .validators import COIN_SYMBOL_PATTERN

ALERT_TYPE_CHOICES = [
    ('above', 'Above Target Price (Take Profit)'),
    ('below', 'Below Target Price (Stop Loss)'),
    ('increase', 'Price Increase'),
    ('decrease', 'Price Decrease'),
]


class AlertConfigForm(forms.Form):
    """Form for creating price threshold alerts via standard Django views."""

    coin_symbol = forms.CharField(
        label="Coin Symbol",
        max_length=10,
        required=True,
        strip=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. BTC, ETH',
            'class': 'form-input',
        }),
    )
    target_price = forms.FloatField(
        label="Target Price ($)",
        required=True,
        min_value=0.0001,
        widget=forms.NumberInput(attrs={
            'placeholder': 'e.g. 68000',
            'step': 'any',
            'class': 'form-input',
        }),
    )
    alert_type = forms.ChoiceField(
        label="Condition",
        choices=ALERT_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def clean_coin_symbol(self) -> str:
        raw = (self.cleaned_data.get('coin_symbol') or '').strip().upper()
        if not raw:
            raise forms.ValidationError("Coin symbol is required.")
        if not COIN_SYMBOL_PATTERN.match(raw):
            raise forms.ValidationError("Invalid symbol. Must be 3-10 uppercase letters.")
        return raw

    def to_payload(self) -> dict:
        """Convert validated form data to repository payload."""
        return {
            'symbol': self.cleaned_data['coin_symbol'],
            'target_price': self.cleaned_data['target_price'],
            'alert_type': self.cleaned_data['alert_type'],
        }
