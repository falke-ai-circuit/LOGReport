import re

def apply_ultra_condensed_format(content: str, doc_type: str) -> str:
    """
    Applies ultra-condensed format rules to the document content.
    This is a simplified implementation focusing on a few rules.
    """
    transformed_content = []
    lines = content.split('\n')

    # Apply chain notation for lists
    list_items = []
    for line in lines:
        if line.strip().startswith('- '):
            list_items.append(line.strip()[2:].strip())
        else:
            if list_items:
                transformed_content.append(" • ".join(list_items))
                list_items = []
            transformed_content.append(line)
    if list_items:
        transformed_content.append(" • ".join(list_items))

    # Further transformations can be added here based on doc_type and specific rules
    # For example, converting sections to tables, adding symbols, etc.

    return "\n".join(transformed_content)

def transform_document(file_path: str, doc_type: str) -> str:
    """
    Reads a document, applies the ultra-condensed format, and returns the transformed content.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    transformed_content = apply_ultra_condensed_format(content, doc_type)
    return transformed_content

if __name__ == "__main__":
    # This part is for testing the script directly
    # In the actual workflow, this will be called by another script
    sample_content = """
# Sample Document

This is a sample document with some content.

- Item 1
- Item 2
- Item 3

Another paragraph.

- Sub-item A
- Sub-item B
"""
    
    transformed = apply_ultra_condensed_format(sample_content, "Technical")
    print(transformed)