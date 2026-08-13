"""
Health Check API Route for auth-service
"""
from fastapi import APIRouter, status

router = APIRouter()

@router.get('/health', status_code=status.HTTP_200_OK)
async def get_health():
    return {'status': 'healthy', 'service': 'auth-service'}
