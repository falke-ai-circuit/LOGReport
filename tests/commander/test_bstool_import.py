"""
Unit tests for BsToolCommandService import and instantiation.

Tests verify that BsToolCommandService can be imported and basic
service initialization works correctly.
"""
import os
import sys
import pytest

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_bstool_service_import():
    """Test that BsToolCommandService can be imported without errors"""
    # Direct import to avoid commander module dependencies
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'commander', 'services'))
    from bstool_command_service import BsToolCommandService
    
    # Assertions: Class exists and can be referenced
    assert BsToolCommandService is not None
    assert hasattr(BsToolCommandService, '__init__')
    assert hasattr(BsToolCommandService, '__name__')

def test_bstool_service_instantiation():
    """Test that BsToolCommandService can be instantiated"""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'commander', 'services'))
    from bstool_command_service import BsToolCommandService
    
    # Instantiate service
    service = BsToolCommandService()
    
    # Assertions: Instance created successfully
    assert service is not None
    assert isinstance(service, BsToolCommandService)
    assert hasattr(service, 'execute')  # Should have execute method

def test_bstool_service_type():
    """Test that BsToolCommandService has correct type"""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'commander', 'services'))
    from bstool_command_service import BsToolCommandService
    
    service = BsToolCommandService()
    
    # Assertions: Type checking
    assert type(service).__name__ == 'BsToolCommandService'
    assert str(type(service)) == "<class 'bstool_command_service.BsToolCommandService'>"

if __name__ == "__main__":
    pytest.main([__file__, '-v'])