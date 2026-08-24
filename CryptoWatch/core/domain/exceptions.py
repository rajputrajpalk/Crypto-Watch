class CryptoWatchException(Exception):
    """Base exception for CryptoWatch application domain errors."""


class UnknownCoinSymbolError(CryptoWatchException):
    """Raised when an unknown or unsupported cryptocurrency symbol is requested."""

    def __init__(self, symbol: str):
        super().__init__(f"Unknown coin symbol: {symbol}")
        self.symbol = symbol


class UnsupportedAssetWarning(CryptoWatchException):
    """Raised when an operation targets an asset not found in the live price feed."""

    def __init__(self, symbol: str):
        super().__init__(f"Unsupported asset: {symbol}")
        self.symbol = symbol
