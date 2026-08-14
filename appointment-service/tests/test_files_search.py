import pytest
from src.services.files_search import FilesSearchHandler

def test_files_search_execution():
    handler = FilesSearchHandler()
    result = handler.process({"test_key": "test_value"})
    assert result["status"] == "success"
    assert result["feature"] == "files_search"