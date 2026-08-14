import pytest
from src.services.automated_tests_files import AutomatedTestsFilesSearchHandler

def test_automated_tests_files_execution():
    handler = AutomatedTestsFilesSearchHandler()
    result = handler.process({"test_key": "test_value"})
    assert result["status"] == "success"
    assert result["feature"] == "automated_tests_files"