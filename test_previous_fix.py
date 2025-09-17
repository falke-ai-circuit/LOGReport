#!/usr/bin/env python3
"""
Test script to simulate what the previous fix might have been
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_previous_fixes():
    """
    Test different possible previous fixes
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
    
    # Test 1: cursor.insertText(text + "\n")
    print("Test 1: cursor.insertText(text + '\\n')")
    content = ""
    def insert_text_plus_newline(text):
        nonlocal content
        content += text + "\n"
    
    content = ""
    for output in outputs:
        insert_text_plus_newline(output)
    
    print("Result:", repr(content))
    print("Match:", content == expected)
    print()
    
    # Test 2: cursor.insertText("\n" + text)
    print("Test 2: cursor.insertText('\\n' + text)")
    content = ""
    def insert_newline_plus_text(text):
        nonlocal content
        if content:  # Add newline before text if there's existing content
            content += "\n"
        content += text
    
    content = ""
    for output in outputs:
        insert_newline_plus_text(output)
    
    print("Result:", repr(content))
    print("Match:", content == expected)
    print()
    
    # Test 3: cursor.insertText(text); cursor.insertText("\n")
    print("Test 3: cursor.insertText(text); cursor.insertText('\\n')")
    content = ""
    def insert_text_then_newline(text):
        nonlocal content
        content += text
        content += "\n"
    
    content = ""
    for output in outputs:
        insert_text_then_newline(output)
    
    print("Result:", repr(content))
    print("Match:", content == expected)
    print()
    
    # Test 4: What if we were adding extra newlines?
    print("Test 4: What if we add extra newlines between outputs?")
    content = ""
    first = True
    for output in outputs:
        if not first:
            content += "\n"  # Extra newline between outputs
        content += output
        first = False
    
    print("Result:", repr(content))
    print("Match:", content == expected)
    print()
    
    # Test 5: What if each output already has a newline and we add another?
    print("Test 5: What if outputs already have newlines and we add more?")
    content = ""
    for i, output in enumerate(outputs):
        content += output
        if i < len(outputs) - 1:  # Don't add newline after last output
            content += "\n"  # Extra newline between outputs
    
    print("Result:", repr(content))
    print("Match:", content == expected)
    print()

if __name__ == "__main__":
    print("Testing possible previous fixes")
    print("=" * 50)
    test_previous_fixes()