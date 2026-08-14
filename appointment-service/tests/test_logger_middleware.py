import pytest
from src.middleware.logger_middleware import RequestLoggerMiddleware

def test_logger_initialization():
    mw = RequestLoggerMiddleware()
    assert mw is not None