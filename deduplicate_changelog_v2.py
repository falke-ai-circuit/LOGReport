import hashlib
import re

def deduplicate_changelog(input_file, output_file):
    """
    Remove duplicate sections from CHANGELOG.md while preserving unique content.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split content into lines
    lines = content.split('\n')
    
    # Track unique sections
    seen_sections = set()
    unique_lines = []
    
    # Track current section
    current_section = []
    section_header = ""
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a section header (## or ###)
        if line.strip().startswith('## '):
            # Process the previous section if it exists
            if current_section:
                section_content = '\n'.join(current_section)
                section_hash = hashlib.sha256(section_content.encode('utf-8')).hexdigest()
                
                if section_hash not in seen_sections:
                    seen_sections.add(section_hash)
                    unique_lines.extend(current_section)
            
            # Start new section
            current_section = [line]
            section_header = line.strip()
        elif line.strip().startswith('### '):
            # Process the previous section if it exists
            if current_section:
                section_content = '\n'.join(current_section)
                section_hash = hashlib.sha256(section_content.encode('utf-8')).hexdigest()
                
                if section_hash not in seen_sections:
                    seen_sections.add(section_hash)
                    unique_lines.extend(current_section)
            
            # Start new section
            current_section = [line]
            section_header = line.strip()
        else:
            # Add line to current section
            current_section.append(line)
        
        i += 1
    
    # Process the last section
    if current_section:
        section_content = '\n'.join(current_section)
        section_hash = hashlib.sha256(section_content.encode('utf-8')).hexdigest()
        
        if section_hash not in seen_sections:
            seen_sections.add(section_hash)
            unique_lines.extend(current_section)
    
    # Remove excessive empty lines (more than 2 consecutive empty lines)
    cleaned_lines = []
    empty_line_count = 0
    
    for line in unique_lines:
        if not line.strip():
            empty_line_count += 1
            if empty_line_count <= 2:  # Keep up to 2 consecutive empty lines
                cleaned_lines.append(line)
        else:
            empty_line_count = 0
            cleaned_lines.append(line)
    
    # Write the deduplicated content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines))
    
    print(f"Deduplicated CHANGELOG written to {output_file}")
    print(f"Original lines: {len(lines)}")
    print(f"Unique lines: {len(cleaned_lines)}")

if __name__ == "__main__":
    deduplicate_changelog("CHANGELOG.md", "CHANGELOG_deduplicated_v2.md")