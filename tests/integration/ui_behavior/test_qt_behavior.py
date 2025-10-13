# Simple test to understand Qt behavior without actually running Qt
def simulate_qt_textedit_behavior():
    """Simulate what might be happening with Qt's QTextEdit"""
    
    # Simulate the QTextEdit content
    content = ""
    
    def insert_text_at_end(text):
        """Simulate inserting text at the end of QTextEdit"""
        nonlocal content
        content += text
    
    # Test case from the failing test
    outputs = [
        "First output line\n",
        "Second output line\n", 
        "Third output line\n"
    ]
    
    # Clear content
    content = ""
    
    # Simulate appending each output
    for output in outputs:
        insert_text_at_end(output)
    
    print("Simulation of Qt behavior:")
    print(f"Result: {repr(content)}")
    print(f"Expected: {repr(''.join(outputs))}")
    print(f"Match: {content == ''.join(outputs)}")
    print()
    
    # This shows that if Qt just appends text as-is, there should be no extra newlines
    # So the issue must be something else

if __name__ == "__main__":
    simulate_qt_textedit_behavior()