"""
Unit tests for report generation improvements: node grouping, TOC, and line wrapping.
Tests validate node-based organization, bookmark/TOC generation, and intelligent line wrapping.
"""

import pytest
from pathlib import Path
import tempfile
import os
from src.generator import ReportGenerator
from reportlab.lib.pagesizes import A4


class TestNodeExtraction:
    """Test node name extraction from filenames"""
    
    def test_extract_ap_node_with_m_suffix(self):
        """Should extract AP01m from filename"""
        gen = ReportGenerator()
        result = gen.extract_node_from_filename("AP01m_192_168_0_11-162.fbc")
        assert result == "AP01M"
    
    def test_extract_ap_node_with_r_suffix(self):
        """Should extract AP02r from filename"""
        gen = ReportGenerator()
        result = gen.extract_node_from_filename("AP02r_192_168_0_12.rpc")
        assert result == "AP02R"
    
    def test_extract_ap_node_without_suffix(self):
        """Should extract AP03 from filename"""
        gen = ReportGenerator()
        result = gen.extract_node_from_filename("AP03_test.log")
        assert result == "AP03"
    
    def test_extract_al_node(self):
        """Should extract AL01 from filename"""
        gen = ReportGenerator()
        result = gen.extract_node_from_filename("AL01_debug.lis")
        assert result == "AL01"
    
    def test_extract_unknown_node(self):
        """Should return 'Unknown' for unrecognized pattern"""
        gen = ReportGenerator()
        result = gen.extract_node_from_filename("random_file.log")
        assert result == "Unknown"
    
    def test_extract_case_insensitive(self):
        """Should handle lowercase node names"""
        gen = ReportGenerator()
        result = gen.extract_node_from_filename("ap01m_test.fbc")
        assert result == "AP01M"


class TestLogGrouping:
    """Test grouping logs by node and file type"""
    
    def test_group_single_node_multiple_types(self):
        """Should group different file types under same node"""
        gen = ReportGenerator()
        logs = [
            {'filename': 'AP01m_test.fbc', 'content': ['line1']},
            {'filename': 'AP01m_test.rpc', 'content': ['line2']},
            {'filename': 'AP01m_test.log', 'content': ['line3']},
        ]
        
        grouped = gen.group_logs_by_node(logs)
        
        assert 'AP01M' in grouped
        assert len(grouped['AP01M']['.fbc']) == 1
        assert len(grouped['AP01M']['.rpc']) == 1
        assert len(grouped['AP01M']['.log']) == 1
        assert len(grouped['AP01M']['.lis']) == 0
    
    def test_group_multiple_nodes(self):
        """Should separate logs by node name"""
        gen = ReportGenerator()
        logs = [
            {'filename': 'AP01m_test.fbc', 'content': ['line1']},
            {'filename': 'AP02m_test.fbc', 'content': ['line2']},
            {'filename': 'AL01_test.log', 'content': ['line3']},
        ]
        
        grouped = gen.group_logs_by_node(logs)
        
        assert len(grouped) == 3
        assert 'AP01M' in grouped
        assert 'AP02M' in grouped
        assert 'AL01' in grouped
    
    def test_group_preserves_file_type_order(self):
        """Should maintain file type order constant"""
        gen = ReportGenerator()
        
        # Verify TYPE_ORDER exists and has correct ordering
        assert gen.TYPE_ORDER['.fbc'] < gen.TYPE_ORDER['.rpc']
        assert gen.TYPE_ORDER['.rpc'] < gen.TYPE_ORDER['.log']
        assert gen.TYPE_ORDER['.log'] < gen.TYPE_ORDER['.lis']
    
    def test_group_handles_unknown_file_type(self):
        """Should fallback to .log for unknown extensions"""
        gen = ReportGenerator()
        logs = [
            {'filename': 'AP01m_test.unknown', 'content': ['line1']},
        ]
        
        grouped = gen.group_logs_by_node(logs)
        
        assert len(grouped['AP01M']['.log']) == 1


class TestLineWrapping:
    """Test intelligent line wrapping for long lines"""
    
    def test_wrap_single_long_line(self):
        """Should wrap lines longer than max_width"""
        gen = ReportGenerator()
        content = ["This is a very long line that definitely exceeds ninety characters and should be wrapped at word boundaries to prevent information loss"]
        
        wrapped = gen.wrap_long_lines(content, max_width=90)
        
        assert len(wrapped) > 1
        assert all(len(line) <= 90 for line in wrapped)
    
    def test_wrap_preserves_short_lines(self):
        """Should not modify lines shorter than max_width"""
        gen = ReportGenerator()
        content = ["Short line", "Another short line"]
        
        wrapped = gen.wrap_long_lines(content, max_width=90)
        
        assert wrapped == content
    
    def test_wrap_mixed_lengths(self):
        """Should only wrap long lines, preserve short ones"""
        gen = ReportGenerator()
        short_line = "Short"
        long_line = "A" * 150  # Very long line
        content = [short_line, long_line, "Another short"]
        
        wrapped = gen.wrap_long_lines(content, max_width=90)
        
        assert wrapped[0] == short_line
        assert len(wrapped) > 3  # Long line should be split
        assert wrapped[-1] == "Another short"
    
    def test_wrap_at_word_boundaries(self):
        """Should wrap at word boundaries, not mid-word"""
        gen = ReportGenerator()
        content = ["This is a line with many words that should wrap at word boundaries not in the middle of words"]
        
        wrapped = gen.wrap_long_lines(content, max_width=50)
        
        # Check that no line ends with a partial word (simple heuristic)
        for line in wrapped[:-1]:  # Exclude last line
            assert line.endswith(' ') or len(line) == 50 or line == content[0][:50]
    
    def test_wrap_empty_content(self):
        """Should handle empty content list"""
        gen = ReportGenerator()
        content = []
        
        wrapped = gen.wrap_long_lines(content, max_width=90)
        
        assert wrapped == []
    
    def test_wrap_default_width(self):
        """Should use default width of 80 characters (A4 page calculation)"""
        gen = ReportGenerator()
        content = ["A" * 120]  # Longer than default
        
        wrapped = gen.wrap_long_lines(content)  # No max_width specified
        
        assert len(wrapped) > 1
        assert all(len(line) <= 80 for line in wrapped)


class TestPDFGeneration:
    """Test PDF generation with node grouping and bookmarks"""
    
    def test_pdf_creates_file(self):
        """Should create PDF file at specified path"""
        gen = ReportGenerator()
        logs = [
            {'filename': 'AP01m_test.fbc', 'content': ['Test content']},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_report.pdf')
            gen.generate_pdf(logs, output_path)
            
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
    
    def test_pdf_groups_by_node(self):
        """Should organize content by node in PDF"""
        gen = ReportGenerator()
        logs = [
            {'filename': 'AP01m_test.fbc', 'content': ['AP01 FBC content']},
            {'filename': 'AP02m_test.fbc', 'content': ['AP02 FBC content']},
            {'filename': 'AP01m_test.log', 'content': ['AP01 LOG content']},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_grouped.pdf')
            gen.generate_pdf(logs, output_path)
            
            # PDF should be created successfully
            assert os.path.exists(output_path)
    
    def test_pdf_wraps_long_lines(self):
        """Should wrap long lines in PDF generation"""
        gen = ReportGenerator()
        long_line = "A" * 200  # Very long line
        logs = [
            {'filename': 'AP01m_test.log', 'content': [long_line]},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_wrapped.pdf')
            gen.generate_pdf(logs, output_path)
            
            assert os.path.exists(output_path)


class TestDOCXGeneration:
    """Test DOCX generation with node grouping and TOC"""
    
    def test_docx_creates_file(self):
        """Should create DOCX file at specified path"""
        gen = ReportGenerator()
        logs = [
            {'filename': 'AP01m_test.fbc', 'content': ['Test content']},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_report.docx')
            gen.generate_docx(logs, output_path)
            
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
    
    def test_docx_groups_by_node(self):
        """Should organize content by node in DOCX"""
        gen = ReportGenerator()
        logs = [
            {'filename': 'AP01m_test.fbc', 'content': ['AP01 FBC content']},
            {'filename': 'AP02m_test.fbc', 'content': ['AP02 FBC content']},
            {'filename': 'AP01m_test.log', 'content': ['AP01 LOG content']},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_grouped.docx')
            gen.generate_docx(logs, output_path)
            
            # DOCX should be created successfully
            assert os.path.exists(output_path)
    
    def test_docx_wraps_long_lines(self):
        """Should wrap long lines in DOCX generation"""
        gen = ReportGenerator()
        long_line = "A" * 200  # Very long line
        logs = [
            {'filename': 'AP01m_test.log', 'content': [long_line]},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_wrapped.docx')
            gen.generate_docx(logs, output_path)
            
            assert os.path.exists(output_path)


class TestIntegration:
    """Integration tests for complete report generation workflow"""
    
    def test_complete_workflow_pdf(self):
        """Should generate complete PDF report with all features"""
        gen = ReportGenerator()
        logs = [
            {'filename': 'AP01m_192_168_0_11-162.fbc', 'content': ['FBC line 1', 'FBC line 2']},
            {'filename': 'AP01m_192_168_0_11-162.rpc', 'content': ['RPC line 1']},
            {'filename': 'AP01m_test.log', 'content': ['LOG line 1', 'A' * 150]},  # Contains long line
            {'filename': 'AP02m_test.fbc', 'content': ['AP02 FBC content']},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'complete_report.pdf')
            gen.generate_pdf(logs, output_path)
            
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 1000  # Should have substantial content
    
    def test_complete_workflow_docx(self):
        """Should generate complete DOCX report with all features"""
        gen = ReportGenerator()
        logs = [
            {'filename': 'AP01m_192_168_0_11-162.fbc', 'content': ['FBC line 1', 'FBC line 2']},
            {'filename': 'AP01m_192_168_0_11-162.rpc', 'content': ['RPC line 1']},
            {'filename': 'AP01m_test.log', 'content': ['LOG line 1', 'A' * 150]},  # Contains long line
            {'filename': 'AP02m_test.fbc', 'content': ['AP02 FBC content']},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'complete_report.docx')
            gen.generate_docx(logs, output_path)
            
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 1000  # Should have substantial content
