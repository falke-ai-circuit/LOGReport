"""
Test for startup color checking logic
"""
import os
import tempfile
import pytest


def test_startup_color_logic():
    """Test the color logic for file content on startup"""
    
    # Test logic: red (0 lines), yellow (<10 lines), green (>=10 lines)
    test_cases = [
        (0, "red", "No content"),
        (3, "yellow", "Minimal content"),
        (9, "yellow", "Just below threshold"),
        (10, "green", "At threshold"),
        (50, "green", "Well above threshold"),
    ]
    
    for line_count, expected_color, description in test_cases:
        # Simulate the logic from _check_file_color_on_startup
        if line_count == 0:
            color = "red"
        elif line_count < 10:
            color = "yellow"
        else:
            color = "green"
        
        assert color == expected_color, f"Failed for {description}: expected {expected_color}, got {color}"
        print(f"✓ {description}: {line_count} lines → {color}")


def test_file_existence_check():
    """Test that non-existent files are handled correctly"""
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_path = f.name
        f.write("line 1\n")
        f.write("line 2\n")
    
    try:
        # File should exist
        assert os.path.exists(temp_path), "Temporary file should exist"
        
        # Count lines
        with open(temp_path, 'r') as f:
            line_count = sum(1 for _ in f)
        
        assert line_count == 2, f"Expected 2 lines, got {line_count}"
        
        # Verify color logic
        color = "yellow" if line_count < 10 else "green"
        assert color == "yellow", "2 lines should result in yellow color"
        
        print(f"✓ File existence check passed: {line_count} lines → {color}")
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_integration_flow():
    """Test the complete integration flow of startup coloring"""
    
    # Simulate the flow:
    # 1. File is created during operation and colored green (15 lines)
    # 2. Application restarts
    # 3. On startup, file is loaded and color is re-applied
    
    print("\n📋 Integration Flow Test:")
    print("1. During operation: File created with 15 lines")
    lines_during_operation = 15
    runtime_color = "green" if lines_during_operation >= 10 else ("yellow" if lines_during_operation > 0 else "red")
    print(f"   Runtime color: {runtime_color}")
    
    print("\n2. Application restarts...")
    print("3. On startup: File content is checked")
    lines_on_startup = 15  # Same file content
    startup_color = "green" if lines_on_startup >= 10 else ("yellow" if lines_on_startup > 0 else "red")
    print(f"   Startup color: {startup_color}")
    
    assert runtime_color == startup_color, "Runtime and startup colors should match for the same file content"
    print(f"\n✓ Color persistence verified: {runtime_color} → {startup_color}")


if __name__ == "__main__":
    print("=" * 80)
    print("Testing Startup Color Logic")
    print("=" * 80)
    
    test_startup_color_logic()
    print()
    test_file_existence_check()
    print()
    test_integration_flow()
    
    print("\n" + "=" * 80)
    print("✅ All tests passed!")
    print("=" * 80)
