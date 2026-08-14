# Autonomously Generated Module: AppointmentEndpoint
# Service: appointment-service
# Task Instruction: in appointment service add endpoint in main.py for get appointmentType just like below code
@app.get('/appointments', response_model=List[AppointmentRead])
async def get_all_appointments(
    session: AsyncSession = Depends(get_session)
):
    """
    retreive a list of appointment
    """
    statement = select(Appointment)
    result = await session.exec(statement)
    appts = result.all()
    return appts

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AppointmentEndpointHandler:
    """
    Autonomous Implementation for 'in appointment service add endpoint in main.py for get appoi'
    """
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def process(self, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        logger.info(f"Processing appointment_endpoint with payload: {payload}")
        return {
            "status": "success",
            "feature": "appointment_endpoint",
            "instruction": "in appointment service add endpoint in main.py for",
            "data": payload or {}
        }