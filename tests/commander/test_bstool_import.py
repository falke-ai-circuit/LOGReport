"""
Simple test to verify BsToolCommandService can be imported and instantiated
"""
import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_bstool_import():
    """Test that BsToolCommandService can be imported"""
    try:
        # Direct import to avoid commander module dependencies
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'commander', 'services'))
        from bstool_command_service import BsToolCommandService
        service = BsToolCommandService()
        assert service is not None
        print("BsToolCommandService imported and instantiated successfully")
    except Exception as e:
        print(f"Failed to import BsToolCommandService: {e}")
        raise

if __name__ == "__main__":
    test_bstool_import()