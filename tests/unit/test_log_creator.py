"""
Unit tests for LogCreator module.

Tests verify log file and directory structure creation functionality,
including FBC/RPC file generation with proper naming conventions.
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from src.log_creator import LogCreator


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test output files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_nodes():
    """Sample node data for testing."""
    return [
        {
            'name': 'TestNode1',
            'ip': '192.168.1.100',
            'types': ['FBC', 'RPC'],
            'tokens': ['T001', 'T002', 'T003']
        },
        {
            'name': 'TestNode2',
            'ip': '10.0.0.50',
            'types': ['FBC'],
            'tokens': ['T100']
        },
        {
            'name': 'NodeWithoutTypes',
            'ip': '172.16.0.1',
            'types': [],
            'tokens': []
        }
    ]


@pytest.fixture
def content_template():
    """Sample content template for log files."""
    return "Generated: $DATETIME\nFile: $FILENAME\nContent placeholder"


class TestLogCreatorFileStructure:
    """Tests for file structure creation."""

    def test_create_file_structure_basic(self, temp_output_dir, sample_nodes, content_template):
        """Test basic file structure creation with valid nodes."""
        results = LogCreator.create_file_structure(temp_output_dir, sample_nodes, content_template)
        
        # Assertions: Files created successfully
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # Verify output directory exists
        assert os.path.exists(temp_output_dir)
        assert os.path.isdir(temp_output_dir)

    def test_fbc_directory_creation(self, temp_output_dir, sample_nodes, content_template):
        """Test FBC directory and file creation."""
        LogCreator.create_file_structure(temp_output_dir, sample_nodes, content_template)
        
        # Assertions: FBC directory structure exists
        fbc_dir = Path(temp_output_dir) / "FBC"
        assert fbc_dir.exists()
        assert fbc_dir.is_dir()
        
        # Verify node subdirectories
        node1_dir = fbc_dir / "TestNode1"
        assert node1_dir.exists()
        assert node1_dir.is_dir()

    def test_rpc_directory_creation(self, temp_output_dir, sample_nodes, content_template):
        """Test RPC directory and file creation."""
        LogCreator.create_file_structure(temp_output_dir, sample_nodes, content_template)
        
        # Assertions: RPC directory structure exists
        rpc_dir = Path(temp_output_dir) / "RPC"
        assert rpc_dir.exists()
        assert rpc_dir.is_dir()

    def test_file_naming_convention(self, temp_output_dir, sample_nodes, content_template):
        """Test that files follow naming convention: NodeName_IP_Token.ext"""
        LogCreator.create_file_structure(temp_output_dir, sample_nodes, content_template)
        
        # Check FBC file naming (IP with hyphens)
        fbc_files = list(Path(temp_output_dir).glob("FBC/TestNode1/*.fbc"))
        assert len(fbc_files) > 0
        
        # Assertions: Filename format correct
        for fbc_file in fbc_files:
            assert "TestNode1" in fbc_file.name
            assert "192-168-1-100" in fbc_file.name  # IP with hyphens
            assert fbc_file.suffix == ".fbc"

    def test_content_template_substitution(self, temp_output_dir, sample_nodes, content_template):
        """Test that template variables are substituted in file content."""
        LogCreator.create_file_structure(temp_output_dir, sample_nodes, content_template)
        
        fbc_files = list(Path(temp_output_dir).glob("FBC/**/*.fbc"))
        assert len(fbc_files) > 0
        
        # Read first file and check content
        with open(fbc_files[0], 'r') as f:
            content = f.read()
        
        # Assertions: Template variables replaced
        assert "$DATETIME" not in content, "DATETIME placeholder should be replaced"
        assert "$FILENAME" not in content, "FILENAME placeholder should be replaced"
        assert "Generated:" in content
        assert "File:" in content

    def test_skip_nodes_without_types(self, temp_output_dir, sample_nodes, content_template):
        """Test that nodes without types are skipped."""
        results = LogCreator.create_file_structure(temp_output_dir, sample_nodes, content_template)
        
        # Assertions: Node without types doesn't create files
        all_files = list(Path(temp_output_dir).rglob("*"))
        node_without_types_files = [f for f in all_files if "NodeWithoutTypes" in str(f)]
        assert len(node_without_types_files) == 0, "Nodes without types should not create files"

    def test_max_three_tokens_per_node(self, temp_output_dir, sample_nodes, content_template):
        """Test that only first 3 tokens are processed per node."""
        # Add node with many tokens
        nodes = [{
            'name': 'NodeManyTokens',
            'ip': '192.168.1.1',
            'types': ['FBC'],
            'tokens': ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
        }]
        
        LogCreator.create_file_structure(temp_output_dir, nodes, content_template)
        
        fbc_files = list(Path(temp_output_dir).glob("FBC/NodeManyTokens/*.fbc"))
        
        # Assertions: Only 3 files created (max token limit)
        assert len(fbc_files) == 3, "Should create max 3 files per node type"

    def test_empty_nodes_list(self, temp_output_dir, content_template):
        """Test handling of empty nodes list."""
        results = LogCreator.create_file_structure(temp_output_dir, [], content_template)
        
        # Assertions: Returns empty dict, creates output dir
        assert isinstance(results, dict)
        assert len(results) == 0
        assert os.path.exists(temp_output_dir)

    def test_existing_file_not_overwritten(self, temp_output_dir, sample_nodes, content_template):
        """Test that existing files are not overwritten."""
        # Create file structure first time
        LogCreator.create_file_structure(temp_output_dir, sample_nodes, content_template)
        
        # Get first file and modify it
        fbc_files = list(Path(temp_output_dir).glob("FBC/**/*.fbc"))
        test_file = fbc_files[0]
        original_content = test_file.read_text()
        
        # Modify the file
        test_file.write_text("MODIFIED CONTENT")
        
        # Create file structure again
        LogCreator.create_file_structure(temp_output_dir, sample_nodes, content_template)
        
        # Assertions: File not overwritten (modified content preserved)
        current_content = test_file.read_text()
        assert current_content == "MODIFIED CONTENT", "Existing files should not be overwritten"
        assert current_content != original_content


class TestLogCreatorEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_node_name_with_spaces(self, temp_output_dir, content_template):
        """Test handling of node names with spaces."""
        nodes = [{
            'name': 'Node With Spaces',
            'ip': '192.168.1.1',
            'types': ['FBC'],
            'tokens': ['T1']
        }]
        
        LogCreator.create_file_structure(temp_output_dir, nodes, content_template)
        
        # Assertions: Spaces replaced with underscores
        node_dir = Path(temp_output_dir) / "FBC" / "Node_With_Spaces"
        assert node_dir.exists(), "Spaces should be replaced with underscores"

    def test_missing_ip_field(self, temp_output_dir, content_template):
        """Test handling of nodes without IP field (uses default)."""
        nodes = [{
            'name': 'NoIPNode',
            'types': ['FBC'],
            'tokens': ['T1']
        }]
        
        LogCreator.create_file_structure(temp_output_dir, nodes, content_template)
        
        # Assertions: Uses default IP
        fbc_files = list(Path(temp_output_dir).glob("FBC/NoIPNode/*.fbc"))
        assert len(fbc_files) > 0
        assert "192-168-0-1" in fbc_files[0].name, "Should use default IP"

    def test_nested_directory_creation(self, temp_output_dir, sample_nodes, content_template):
        """Test creation of nested directory structures."""
        deep_path = os.path.join(temp_output_dir, "level1", "level2", "level3")
        
        LogCreator.create_file_structure(deep_path, sample_nodes, content_template)
        
        # Assertions: Deep directory structure created
        assert os.path.exists(deep_path)
        assert os.path.exists(os.path.join(deep_path, "FBC"))
        assert os.path.exists(os.path.join(deep_path, "RPC"))


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
