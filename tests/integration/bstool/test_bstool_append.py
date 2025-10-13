#!/usr/bin/env python3
"""
Test script to verify the behavior of the append_output method
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_append_behavior():
    """
    Test the behavior of appending text without Qt
    """
    # Simulate the test case that's failing
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
    
    # Simulate what happens with our current approach
    # This is a simplified simulation of what QTextEdit.append() might do
    # QTextEdit.append() adds the text as a new paragraph, which means it adds a newline
    # before the text if there's existing text
    
    # Let's simulate the current behavior
    content = ""
    
    def simulate_append(text):
        """Simulate QTextEdit.append() behavior"""
        nonlocal content
        if content and not content.endswith('\n'):
            content += '\n'
        content += text
        if not content.endswith('\n'):
            content += '\n'
    
    # Clear content
    content = ""
    
    # Simulate appending each output
    for output in outputs:
        simulate_append(output)
    
    print("Simulated QTextEdit.append() result:")
    print(repr(content))
    print()
    
    # Check if they match
    print(f"Match: {content == expected}")
    
    if content != expected:
        print("ISSUE: Extra newlines are being added!")
        print("Expected:", repr(expected))
        print("Actual:  ", repr(content))
    
    return content == expected

def test_direct_insert():
    """
    Test direct text insertion without adding newlines
    """
    # Simulate the test case that's failing
    outputs = [
        "First output line\n",
        "Second output line\n",
        "Third output line\n"
    ]
    
    # Expected result (what we want)
    expected = "".join(outputs)
    print("\nExpected result:")
    print(repr(expected))
    print()
    
    # Simulate direct insertion (what we were doing before)
    content = ""
    
    def simulate_insert_text(text):
        """Simulate cursor.insertText() behavior"""
        nonlocal content
        content += text
    
    # Clear content
    content = ""
    
    # Simulate inserting each output
    for output in outputs:
        simulate_insert_text(output)
    
    print("Simulated cursor.insertText() result:")
    print(repr(content))
    print()
    
    # Check if they match
    print(f"Match: {content == expected}")
    
    if content != expected:
        print("ISSUE: This approach has problems too!")
        print("Expected:", repr(expected))
        print("Actual:  ", repr(content))
    
    return content == expected

if __name__ == "__main__":
    print("Testing BSTool append_output behavior")
    print("=" * 50)
    
    # Test 1: QTextEdit.append() approach
    result1 = test_append_behavior()
    
    # Test 2: Direct insertion approach
    result2 = test_direct_insert()
    
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"QTextEdit.append() approach works: {result1}")
    print(f"Direct insertion approach works: {result2}")