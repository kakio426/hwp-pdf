"""Custom exceptions for HWP converter"""


class HwpConverterError(Exception):
    """Base exception for HWP converter errors"""
    pass


class HwpInitializationError(HwpConverterError):
    """Raised when HWP OLE object fails to initialize"""
    pass


class HwpConversionError(HwpConverterError):
    """Raised when file conversion fails"""
    pass


class HwpTimeoutError(HwpConverterError):
    """Raised when conversion exceeds timeout"""
    pass
