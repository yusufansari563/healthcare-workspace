import pytest
from src.services.appointment_endpoint import AppointmentEndpointHandler

def test_appointment_endpoint_execution():
    handler = AppointmentEndpointHandler()
    result = handler.process({"test_key": "test_value"})
    assert result["status"] == "success"
    assert result["feature"] == "appointment_endpoint"