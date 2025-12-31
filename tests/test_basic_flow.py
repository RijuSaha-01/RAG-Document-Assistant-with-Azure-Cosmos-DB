
import pytest
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.document_loader import DocumentLoader

def test_document_loader_init():
    loader = DocumentLoader()
    assert loader is not None

def test_config_import():
    from src.config import Config
    # Just checking we can import it and access a property
    assert hasattr(Config, 'DATA_DIR')
