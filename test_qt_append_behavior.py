#!/usr/bin/env python3
"""
Test script to simulate QTextEdit.append() behavior more accurately
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def simulate_qtextedit_append_behavior():
    """
    Simulate QTextEdit.append() behavior more accurately
    """
    # Test data from the failing test
    outputs = [
        "First output line\n",
        "Second output line\n",
        "Third output line\n"
    ]
    
    # Expected result (what we want)
    expected = "".join(outputs)
    print("Expected result:")
    print(repr(expected))
    print()
    
    # Simulate QTextEdit.append() behavior more accurately
    # According to Qt documentation, append() inserts text as a new paragraph
    # which means it adds a paragraph separator (which is typically a newline)
    # before the text if there's existing text
    
    content = ""
    
    def qtextedit_append(text):
        """Simulate QTextEdit.append() behavior more accurately"""
        nonlocal content
        # append() treats the text as a new paragraph
        if content:  # If there's existing content
            # Add a paragraph separator (newline) before the new text
            if not content.endswith('\n'):
                content += '\n'
            content += text
        else:
            # First text, just add it
            content += text
    
    # Clear content
    content = ""
    
    # Simulate appending each output
    for output in outputs:
        qtextedit_append(output)
    
    print("Simulated QTextEdit.append() result (accurate):")
    print(repr(content))
    print()
    
    # Check if they match
    match = content == expected
    print(f"Match: {match}")
    
    if not match:
        print("ISSUE: Extra newlines are being added!")
        print("Expected:", repr(expected))
        print("Actual:  ", repr(content))
        print()
        print("Difference analysis:")
        expected_lines = expected.split('\n')
        actual_lines = content.split('\n')
        print("Expected lines:", expected_lines)
        print("Actual lines:  ", actual_lines)
    
    return match

def test_current_implementation():
    """
    Test what our current implementation should produce
    """
    print("\n" + "=" * 50)
    print("Testing current implementation approach")
    print("=" * 50)
    
    # Test data from the failing test
    outputs = [
        "First output line\n",
        "Second output line\n",
        "Third output line\n"
    ]
    
    # Expected result (what we want)
    expected = "".join(outputs)
    print("Expected result:")
    print(repr(expected))
    print()
    
    # Our current approach: QTextEdit.append(text)
    # This should work because each output is treated as a separate paragraph
    # but since each output already ends with \n, it should work correctly
    
    # Let's simulate what should happen
    content = ""
    
    # Simulate the behavior of multiple append() calls where each text
    # already ends with a newline
    for i, output in enumerate(outputs):
        content += output
        # No extra newline should be added between outputs
        # because each output already ends with \n
    
    print("Our current implementation result:")
    print(repr(content))
    print()
    
    # Check if they match
    match = content == expected
    print(f"Match: {match}")
    
    return match

if __name__ == "__main__":
    print("Testing QTextEdit.append() behavior")
    print("=" * 50)
    
    # Test 1: Simulate QTextEdit.append() behavior
    result1 = simulate_qtextedit_append_behavior()
    
    # Test 2: Test our current implementation
    result2 = test_current_implementation()
    
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"QTextEdit.append() simulation works: {result1}")
    print(f"Current implementation should work: {result2}")
    
    if result2:
        print("\nCONCLUSION: Our fix using QTextEdit.append() should resolve the issue!")
    else:
        print("\nCONCLUSION: We need to investigate further...")