import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QTextEdit
from PyQt6.QtGui import QTextCursor

def test_append_output_behavior():
    """Test the behavior of our append_output implementation"""
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create a QTextEdit widget for testing
    text_edit = QTextEdit()
    
    def append_output(text):
        """Our implementation of append_output"""
        cursor = text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Check if we need to add a newline before inserting the text
        # Only add a newline if:
        # 1. There's existing text in the output
        # 2. The existing text doesn't already end with a newline
        # 3. The new text doesn't start with a newline
        if (cursor.position() > 0 and 
            not text_edit.toPlainText().endswith('\n') and 
            text and not text.startswith('\n')):
            cursor.insertText('\n')
        
        cursor.insertText(text)
        text_edit.setTextCursor(cursor)
    
    # Test case 1: Multiple outputs with newlines
    outputs = [
        "First output line\n",
        "Second output line\n", 
        "Third output line\n"
    ]
    
    # Clear the text edit
    text_edit.clear()
    
    # Append each output
    for output in outputs:
        append_output(output)
    
    # Get the final text
    result = text_edit.toPlainText()
    expected = "".join(outputs)
    
    print("Test case 1 - Multiple outputs with newlines:")
    print(f"Result: {repr(result)}")
    print(f"Expected: {repr(expected)}")
    print(f"Match: {result == expected}")
    print()
    
    # Test case 2: Outputs without trailing newlines
    outputs2 = [
        "First output line",
        "Second output line", 
        "Third output line"
    ]
    
    # Clear the text edit
    text_edit.clear()
    
    # Append each output
    for output in outputs2:
        append_output(output)
    
    # Get the final text
    result2 = text_edit.toPlainText()
    expected2 = "\n".join(outputs2) + "\n"  # Should add newlines between outputs
    
    print("Test case 2 - Outputs without trailing newlines:")
    print(f"Result: {repr(result2)}")
    print(f"Expected: {repr(expected2)}")
    print(f"Match: {result2 == expected2}")
    print()
    
    # Test case 3: Mixed outputs
    outputs3 = [
        "First output line\n",
        "Second output line", 
        "Third output line\n"
    ]
    
    # Clear the text edit
    text_edit.clear()
    
    # Append each output
    for output in outputs3:
        append_output(output)
    
    # Get the final text
    result3 = text_edit.toPlainText()
    expected3 = "First output line\n\nSecond output line\nThird output line\n"  # Should add newline between 1st and 2nd
    
    print("Test case 3 - Mixed outputs:")
    print(f"Result: {repr(result3)}")
    print(f"Expected: {repr(expected3)}")
    print(f"Match: {result3 == expected3}")

if __name__ == "__main__":
    test_append_output_behavior()