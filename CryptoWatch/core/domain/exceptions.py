class UnknownCoinSymbolError(Exception):
    """Raised when an unknown/unsupported coin symbol is used."""

    def __init__(self, symbol: str):
        super().__init__(f"Unknown coin symbol: {symbol}")
        self.symbol = symbol


class UnsupportedAssetWarning(Exception):
    """Raised when an alert targets a symbol that does not exist in the current price stream."""

    def __init__(self, symbol: str):
        super().__init__(f"Unsupported asset: {symbol}")
        self.symbol = symbol




