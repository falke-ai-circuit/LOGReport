import hashlib
import re

def deduplicate_changelog(input_file, output_file):
    """
    Remove duplicate entries from CHANGELOG.md while preserving unique content.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split content into lines
    lines = content.split('\n')
    
    # Track seen lines using their hash
    seen_lines = set()
    unique_lines = []
    
    # Track if we're in a code block
    in_code_block = False
    
    for line in lines:
        # Check if entering or leaving a code block
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            
        # For code blocks and empty lines, always include them
        if in_code_block or not line.strip():
            unique_lines.append(line)
            continue
            
        # Create hash of the line for comparison
        line_hash = hashlib.sha256(line.encode('utf-8')).hexdigest()
        
        # If we haven't seen this line, add it
        if line_hash not in seen_lines:
            seen_lines.add(line_hash)
            unique_lines.append(line)
    
    # Write the deduplicated content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(unique_lines))
    
    print(f"Deduplicated CHANGELOG written to {output_file}")
    print(f"Original lines: {len(lines)}")
    print(f"Unique lines: {len(unique_lines)}")

if __name__ == "__main__":
    deduplicate_changelog("CHANGELOG.md", "CHANGELOG_deduplicated.md")