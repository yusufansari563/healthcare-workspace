import pytest
from src.services.automated_tests_appointment import AutomatedTestsAppointmentEndpointHandler

def test_automated_tests_appointment_execution():
    handler = AutomatedTestsAppointmentEndpointHandler()
    result = handler.process({"test_key": "test_value"})
    assert result["status"] == "success"
    assert result["feature"] == "automated_tests_appointment"