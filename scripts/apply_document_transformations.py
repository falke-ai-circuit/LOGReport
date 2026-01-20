import os
from content_transformer import transform_document

# Define Batch 1 documents and their target templates
BATCH_1_DOCUMENTS = {
    "README.md": "Architecture",
    "TODO.md": "Technical",
    "CHANGELOG.md": "Technical"
}

def apply_transformations_to_batch_1():
    """
    Applies transformations to Batch 1 documents and saves the changes.
    """
    print("Applying transformations to Batch 1 documents...")
    for doc_name, doc_type in BATCH_1_DOCUMENTS.items():
        file_path = os.path.join(".", doc_name) # Assuming documents are in the root directory
        
        if os.path.exists(file_path):
            print(f"Transforming {doc_name} as {doc_type} document...")
            transformed_content = transform_document(file_path, doc_type)
            
            # Overwrite the original file with the transformed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(transformed_content)
            print(f"Successfully transformed and updated {doc_name}.")
        else:
            print(f"Warning: Document {doc_name} not found at {file_path}. Skipping.")
    print("Batch 1 document transformations complete.")

if __name__ == "__main__":
    apply_transformations_to_batch_1()