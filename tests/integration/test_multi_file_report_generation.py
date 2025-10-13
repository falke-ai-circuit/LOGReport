"""
Test suite for multi-file type report generation (.log, .txt, .lis, .fbc, .rpc)
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from src.processor import LogProcessor


class TestMultiFileReportGeneration:
    """Test LogProcessor scanning for multiple file types"""
    
    @pytest.fixture
    def temp_log_directory(self):
        """Create temporary directory with various log file types"""
        temp_dir = tempfile.mkdtemp()
        
        # Create root level files
        (Path(temp_dir) / "test.log").write_text("Log file content\nLine 2\nLine 3")
        (Path(temp_dir) / "test.txt").write_text("Text file content\nLine 2")
        (Path(temp_dir) / "node1_192_168_0_1.lis").write_text("LIS file content\nLine 2\nLine 3\nLine 4")
        (Path(temp_dir) / "node1_192_168_0_1_162.fbc").write_text("FBC file content\nLine 2\nLine 3")
        (Path(temp_dir) / "node1_192_168_0_1_162.rpc").write_text("RPC file content\nLine 2")
        
        # Create subfolder with files
        subfolder = Path(temp_dir) / "subfolder"
        subfolder.mkdir()
        (subfolder / "sub.log").write_text("Subfolder log\nLine 2")
        (subfolder / "sub.fbc").write_text("Subfolder FBC\nLine 2\nLine 3")
        (subfolder / "sub.rpc").write_text("Subfolder RPC\nLine 2")
        (subfolder / "sub.lis").write_text("Subfolder LIS\nLine 2\nLine 3\nLine 4\nLine 5")
        
        # Create nested subfolder
        nested = subfolder / "nested"
        nested.mkdir()
        (nested / "nested.log").write_text("Nested log\nLine 2\nLine 3")
        (nested / "nested.lis").write_text("Nested LIS\nLine 2")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_supported_extensions_includes_all_types(self):
        """Test that LogProcessor supports all required file extensions"""
        processor = LogProcessor()
        
        assert '.log' in processor.supported_ext
        assert '.txt' in processor.supported_ext
        assert '.lis' in processor.supported_ext
        assert '.fbc' in processor.supported_ext
        assert '.rpc' in processor.supported_ext
    
    def test_process_directory_finds_all_file_types(self, temp_log_directory):
        """Test that process_directory finds all supported file types"""
        processor = LogProcessor()
        results = processor.process_directory(temp_log_directory)
        
        # Should find 12 files total (5 root + 4 subfolder + 2 nested + 1 text)
        assert len(results) > 0, "Should find files"
        
        # Extract filenames
        filenames = {r['filename'] for r in results}
        
        # Check for .log files
        assert any('.log' in f for f in filenames), "Should find .log files"
        
        # Check for .txt files
        assert any('.txt' in f for f in filenames), "Should find .txt files"
        
        # Check for .lis files
        assert any('.lis' in f for f in filenames), "Should find .lis files"
        
        # Check for .fbc files
        assert any('.fbc' in f for f in filenames), "Should find .fbc files"
        
        # Check for .rpc files
        assert any('.rpc' in f for f in filenames), "Should find .rpc files"
    
    def test_recursive_subfolder_scanning(self, temp_log_directory):
        """Test that subfolders are scanned recursively"""
        processor = LogProcessor()
        results = processor.process_directory(temp_log_directory)
        
        # Get all paths
        paths = {r['path'] for r in results}
        
        # Should have root, subfolder, and nested paths
        assert len(paths) >= 3, f"Should scan multiple levels, found paths: {paths}"
        
        # Check for nested files
        filenames = {r['filename'] for r in results}
        assert 'nested.log' in filenames, "Should find files in nested subfolders"
        assert 'nested.lis' in filenames, "Should find LIS files in nested subfolders"
    
    def test_file_content_is_read_correctly(self, temp_log_directory):
        """Test that file contents are properly read and stored"""
        processor = LogProcessor()
        results = processor.process_directory(temp_log_directory)
        
        # Find a specific file
        test_log = next((r for r in results if r['filename'] == 'test.log'), None)
        assert test_log is not None, "Should find test.log"
        
        # Check content structure
        assert 'content' in test_log
        assert isinstance(test_log['content'], list), "Content should be a list of lines"
        assert len(test_log['content']) > 0, "Content should not be empty"
        
        # Check first line contains expected text
        content_str = '\n'.join(test_log['content'])
        assert 'Log file content' in content_str, "Should contain expected content"
    
    def test_fbc_file_content(self, temp_log_directory):
        """Test that .fbc files are read correctly"""
        processor = LogProcessor()
        results = processor.process_directory(temp_log_directory)
        
        fbc_files = [r for r in results if r['filename'].endswith('.fbc')]
        assert len(fbc_files) >= 2, "Should find at least 2 FBC files"
        
        # Check one FBC file has content
        fbc_file = fbc_files[0]
        assert 'content' in fbc_file
        assert len(fbc_file['content']) > 0, "FBC file should have content"
        
        content_str = '\n'.join(fbc_file['content'])
        assert 'FBC' in content_str, "FBC file should contain expected text"
    
    def test_rpc_file_content(self, temp_log_directory):
        """Test that .rpc files are read correctly"""
        processor = LogProcessor()
        results = processor.process_directory(temp_log_directory)
        
        rpc_files = [r for r in results if r['filename'].endswith('.rpc')]
        assert len(rpc_files) >= 2, "Should find at least 2 RPC files"
        
        # Check one RPC file has content
        rpc_file = rpc_files[0]
        assert 'content' in rpc_file
        assert len(rpc_file['content']) > 0, "RPC file should have content"
    
    def test_lis_file_content(self, temp_log_directory):
        """Test that .lis files are read correctly"""
        processor = LogProcessor()
        results = processor.process_directory(temp_log_directory)
        
        lis_files = [r for r in results if r['filename'].endswith('.lis')]
        assert len(lis_files) >= 3, "Should find at least 3 LIS files"
        
        # Check one LIS file has content
        lis_file = lis_files[0]
        assert 'content' in lis_file
        assert len(lis_file['content']) > 0, "LIS file should have content"
    
    def test_result_structure_is_consistent(self, temp_log_directory):
        """Test that all results have consistent structure"""
        processor = LogProcessor()
        results = processor.process_directory(temp_log_directory)
        
        required_keys = {'type', 'content', 'filename', 'path'}
        
        for result in results:
            assert required_keys.issubset(result.keys()), \
                f"Result missing required keys: {required_keys - result.keys()}"
            assert result['type'] == 'file'
            assert isinstance(result['content'], list)
            assert isinstance(result['filename'], str)
            assert isinstance(result['path'], str)
    
    def test_empty_directory_returns_empty_list(self):
        """Test that scanning empty directory returns empty list"""
        with tempfile.TemporaryDirectory() as temp_dir:
            processor = LogProcessor()
            results = processor.process_directory(temp_dir)
            assert results == [], "Empty directory should return empty list"
    
    def test_file_count_is_accurate(self, temp_log_directory):
        """Test that all expected files are found"""
        processor = LogProcessor()
        results = processor.process_directory(temp_log_directory)
        
        # Count expected files
        # Root: test.log, test.txt, node1.lis, node1.fbc, node1.rpc = 5
        # Subfolder: sub.log, sub.fbc, sub.rpc, sub.lis = 4
        # Nested: nested.log, nested.lis = 2
        # Total = 11 files (note: .text extension also supported but not created)
        
        assert len(results) == 11, f"Expected 11 files, found {len(results)}"
