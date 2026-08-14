import pytest
from src.services.social_media_field import SocialMediaFieldHandler

def test_social_media_field_execution():
    handler = SocialMediaFieldHandler()
    result = handler.process({"test_key": "test_value"})
    assert result["status"] == "success"
    assert result["feature"] == "social_media_field"