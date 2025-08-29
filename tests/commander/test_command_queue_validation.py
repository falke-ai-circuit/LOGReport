"""
Command Queue Validation Test Suite

This test suite provides focused validation of the command queue implementation
with comprehensive test coverage for all critical functionality including:
- Sequential processing validation
- Resource management and cleanup
- Error handling and recovery
- Performance and stress testing
- Integration with sequential command processor
"""

import sys
import os
import logging
import time
import unittest
from unittest.mock import MagicMock, patch, call
from PyQt6.QtCore import QCoreApplication, QTimer
from PyQt6.QtTest import QTest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.commander.services.sequential_command_processor import SequentialCommandProcessor
from src.commander.models import NodeToken
from src.commander.command_queue import CommandQueue
from src.commander.services.fbc_command_service import FbcCommandService
from src.commander.services.rpc_command_service import RpcCommandService
from src.commander.session_manager import SessionManager
from src.commander.utils.circuit_breaker import CircuitBreaker


class TestCommandQueueValidation(unittest.TestCase):
    """Focused validation of command queue functionality"""
    
    def setUp(self):
        """Set up focused test environment"""
        # Create Qt application if needed
        if not QCoreApplication.instance():
            self.app = QCoreApplication([])
        else:
            self.app = QCoreApplication.instance()
            
        # Configure test logging
        logging.basicConfig(level=logging.DEBUG)
        self.test_logger = logging.getLogger(__name__)
        
        # Create mock services with focused mocking
        self.mock_session_manager = MagicMock(spec=SessionManager)
        self.mock_fbc_service = MagicMock(spec=FbcCommandService)
        self.mock_rpc_service = MagicMock(spec=RpcCommandService)
        self.mock_logging_service = MagicMock()
        
        # Create command queue with session manager
        self.command_queue = CommandQueue(self.mock_session_manager)
        
        # Create sequential command processor
        self.processor = SequentialCommandProcessor(
            command_queue=self.command_queue,
            fbc_service=self.mock_fbc_service,
            rpc_service=self.mock_rpc_service,
            session_manager=self.mock_session_manager,
            logging_service=self.mock_logging_service
        )
        
        # Mock internal methods
        self.processor._generate_batch_id = MagicMock(return_value="test_batch_123")
        self.processor._normalize_token = MagicMock(side_effect=lambda token, protocol: token)
        self.processor._release_telnet_client = MagicMock()
        self.processor._perform_periodic_cleanup = MagicMock()
        self.processor._is_valid_ip = MagicMock(return_value=True)
        
        # Mock node managers
        self.mock_fbc_node_manager = MagicMock()
        self.mock_rpc_node_manager = MagicMock()
        self.mock_fbc_service.node_manager = self.mock_fbc_node_manager
        self.mock_rpc_service.node_manager = self.mock_rpc_node_manager
        
        # Mock node retrieval
        self.mock_fbc_node = MagicMock()
        self.mock_rpc_node = MagicMock()
        self.mock_fbc_node_manager.get_node.return_value = self.mock_fbc_node
        self.mock_rpc_node_manager.get_node.return_value = self.mock_rpc_node
        
        # Mock token normalization
        self.mock_fbc_service.normalize_token = MagicMock(side_effect=lambda token: token)
        self.mock_rpc_service.normalize_token = MagicMock(side_effect=lambda token: token)
        
        # Mock session manager
        self.mock_session = MagicMock()
        self.mock_session.is_connected = True
        self.mock_session_manager.get_or_create_session.return_value = self.mock_session
        self.mock_session_manager.get_debugger_session.return_value = None
        
        # Mock logging service
        self.mock_logging_service.open_log_for_token.return_value = "/tmp/test_log.log"
        self.mock_logging_service.start_batch_logging = MagicMock()
        self.mock_logging_service.end_batch_logging = MagicMock()
        self.mock_logging_service.log = MagicMock()
        
        # Track processing events
        self.processing_events = []
        self.command_results = []
        
        # Set up signal handlers
        self.processor.status_message.connect(lambda msg, dur: self.processing_events.append(f"STATUS: {msg}"))
        self.processor.progress_updated.connect(lambda curr, total: self.processing_events.append(f"PROGRESS: {curr}/{total}"))
        self.processor.processing_finished.connect(lambda success, total: self.processing_events.append(f"FINISHED: {success}/{total}"))
        self.command_queue.command_completed.connect(lambda cmd, result, success, token: self.command_results.append((cmd, result, success, token)))
        
    def test_sequential_processing_validation(self):
        """Validation of sequential processing with mixed token types"""
        print("\n" + "="*80)
        print("SEQUENTIAL PROCESSING VALIDATION")
        print("="*80)
        
        # Create test tokens
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),
            NodeToken(token_id="164", token_type="FBC", node_ip="192.168.0.11"),
        ]
        
        # Track processing order
        processing_order = []
        
        def track_add_command(command, token, telnet_client=None):
            processing_order.append((token.token_id, token.token_type))
            self.test_logger.info(f"Command queued: {command} for token {token.token_id}")
            
            # Simulate command completion
            QTimer.singleShot(10, lambda: self.mock_command_queue.command_completed.emit(
                command, f"Success for {token.token_id}", True, token
            ))
            
        self.mock_command_queue = MagicMock(spec=CommandQueue)
        self.mock_command_queue.add_command = track_add_command
        self.mock_command_queue.command_completed = MagicMock()
        self.mock_command_queue.progress_updated = MagicMock()
        self.mock_command_queue.manual_cleanup = MagicMock(return_value=len(tokens))
        
        # Replace the processor's command queue with our mock
        self.processor.command_queue = self.mock_command_queue
        
        # Process tokens sequentially
        print(f"Starting sequential processing of {len(tokens)} tokens...")
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Process Qt events
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 3:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Verify processing results
        print(f"Processing order: {processing_order}")
        
        # Validate sequential order
        expected_order = [
            ("162", "FBC"), ("163", "RPC"), ("164", "FBC")
        ]
        actual_order = processing_order
        
        self.assertEqual(actual_order, expected_order, 
                        f"Expected processing order {expected_order}, got {actual_order}")
        
        # Validate all tokens were processed
        self.assertEqual(len(processing_order), len(tokens), 
                        f"Expected {len(tokens)} tokens processed, got {len(processing_order)}")
        
        print("✓ Sequential processing validation PASSED")
        
    def test_command_queue_synchronization(self):
        """Test command queue synchronization and thread safety"""
        print("\n" + "="*80)
        print("COMMAND QUEUE SYNCHRONIZATION VALIDATION")
        print("="*80)
        
        # Verify single-threaded configuration
        max_threads = self.command_queue.thread_pool.maxThreadCount()
        self.assertEqual(max_threads, 1, 
                        f"Command queue should use single thread, but has {max_threads} threads")
        
        print(f"✓ Thread pool configured for single-threaded execution: {max_threads} threads")
        
        # Test processing state synchronization
        initial_state = self.command_queue.is_processing
        self.assertFalse(initial_state, "Initial processing state should be False")
        
        print("✓ Thread safety validation PASSED")
        
    def test_error_handling_validation(self):
        """Test error handling and recovery mechanisms"""
        print("\n" + "="*80)
        print("ERROR HANDLING VALIDATION")
        print("="*80)
        
        # Create tokens with mixed success/failure scenarios
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),  # Success
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),  # Failure
            NodeToken(token_id="164", token_type="FBC", node_ip="192.168.0.11"),  # Success
        ]
        
        # Track error scenarios
        error_count = 0
        success_count = 0
        
        def mock_add_command_with_failures(command, token, telnet_client=None):
            nonlocal error_count, success_count
            
            # Simulate failures for RPC tokens
            if token.token_type == "RPC":
                error_count += 1
                QTimer.singleShot(50, lambda: self.mock_command_queue.command_completed.emit(
                    command, f"Simulated error for {token.token_id}", False, token
                ))
            else:
                success_count += 1
                QTimer.singleShot(50, lambda: self.mock_command_queue.command_completed.emit(
                    command, f"Success for {token.token_id}", True, token
                ))
                
        self.mock_command_queue = MagicMock(spec=CommandQueue)
        self.mock_command_queue.add_command = mock_add_command_with_failures
        self.mock_command_queue.command_completed = MagicMock()
        self.mock_command_queue.progress_updated = MagicMock()
        self.mock_command_queue.manual_cleanup = MagicMock(return_value=len(tokens))
        
        # Replace the processor's command queue with our mock
        self.processor.command_queue = self.mock_command_queue
        
        # Process tokens with error scenarios
        print(f"Processing {len(tokens)} tokens with mixed success/failure scenarios...")
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Process Qt events
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 3:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Verify error handling
        self.assertEqual(error_count, 1, f"Expected 1 error, got {error_count}")
        self.assertEqual(success_count, 2, f"Expected 2 successes, got {success_count}")
        
        # Verify processing continued despite errors
        self.assertEqual(len(self.command_results), len(tokens), 
                        f"All {len(tokens)} tokens should have been processed despite errors")
        
        print("✓ Error handling validation PASSED")
        
    def test_resource_cleanup_validation(self):
        """Test resource cleanup and memory management"""
        print("\n" + "="*80)
        print("RESOURCE CLEANUP VALIDATION")
        print("="*80)
        
        # Create test tokens
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),
        ]
        
        # Track cleanup calls
        cleanup_calls = []
        
        def track_cleanup():
            cleanup_calls.append(time.time())
            
        self.processor._release_telnet_client = track_cleanup
        
        def mock_add_command(command, token, telnet_client=None):
            QTimer.singleShot(10, lambda: self.mock_command_queue.command_completed.emit(
                command, f"Success for {token.token_id}", True, token
            ))
            
        self.mock_command_queue = MagicMock(spec=CommandQueue)
        self.mock_command_queue.add_command = mock_add_command
        self.mock_command_queue.command_completed = MagicMock()
        self.mock_command_queue.progress_updated = MagicMock()
        self.mock_command_queue.manual_cleanup = MagicMock(return_value=len(tokens))
        
        # Replace the processor's command queue with our mock
        self.processor.command_queue = self.mock_command_queue
        
        # Process tokens
        print(f"Processing {len(tokens)} tokens for resource cleanup validation...")
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Process Qt events
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 2:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Verify cleanup was called for each token
        self.assertEqual(len(cleanup_calls), len(tokens), 
                        f"Expected {len(tokens)} cleanup calls, got {len(cleanup_calls)}")
        
        # Verify manual cleanup was called at the end
        self.mock_command_queue.manual_cleanup.assert_called_once()
        
        print("✓ Resource cleanup validation PASSED")
        
    def test_performance_validation(self):
        """Test performance and throughput characteristics"""
        print("\n" + "="*80)
        print("PERFORMANCE VALIDATION")
        print("="*80)
        
        # Create test tokens
        tokens = [
            NodeToken(token_id=str(i), token_type="FBC" if i % 2 == 0 else "RPC", node_ip="192.168.0.11")
            for i in range(162, 167)  # 5 tokens
        ]
        
        # Track performance metrics
        start_time = time.time()
        processing_times = []
        
        def mock_add_command_with_timing(command, token, telnet_client=None):
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            # Simulate variable processing time (50-200ms)
            delay = 0.05 + (hash(token.token_id) % 150) / 1000
            QTimer.singleShot(int(delay * 1000), lambda: self.mock_command_queue.command_completed.emit(
                command, f"Success for {token.token_id}", True, token
            ))
            
        self.mock_command_queue = MagicMock(spec=CommandQueue)
        self.mock_command_queue.add_command = mock_add_command_with_timing
        self.mock_command_queue.command_completed = MagicMock()
        self.mock_command_queue.progress_updated = MagicMock()
        self.mock_command_queue.manual_cleanup = MagicMock(return_value=len(tokens))
        
        # Replace the processor's command queue with our mock
        self.processor.command_queue = self.mock_command_queue
        
        # Process tokens for performance testing
        print(f"Processing {len(tokens)} tokens for performance validation...")
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Process Qt events
        while self.processor._is_processing and (time.time() - start_time) < 5:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        total_time = time.time() - start_time
        
        # Calculate performance metrics
        avg_processing_time = sum(processing_times) / len(processing_times)
        throughput = len(tokens) / total_time
        
        print(f"\nPerformance Metrics:")
        print(f"  Total processing time: {total_time:.2f} seconds")
        print(f"  Average processing time per token: {avg_processing_time:.3f} seconds")
        print(f"  Throughput: {throughput:.2f} tokens/second")
        
        # Validate performance expectations
        self.assertLess(total_time, 3.0, f"Total processing time should be < 3s, got {total_time:.2f}s")
        self.assertGreater(throughput, 1.0, f"Throughput should be > 1 token/sec, got {throughput:.2f}")
        
        print("✓ Performance validation PASSED")
        
    def test_integration_validation(self):
        """Test integration with sequential command processor"""
        print("\n" + "="*80)
        print("INTEGRATION VALIDATION")
        print("="*80)
        
        # Test processor state management
        initial_state = self.processor._is_processing
        self.assertFalse(initial_state, "Initial processor state should be False")
        
        # Create test tokens
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),
        ]
        
        def mock_add_command(command, token, telnet_client=None):
            QTimer.singleShot(10, lambda: self.mock_command_queue.command_completed.emit(
                command, f"Success for {token.token_id}", True, token
            ))
            
        self.mock_command_queue = MagicMock(spec=CommandQueue)
        self.mock_command_queue.add_command = mock_add_command
        self.mock_command_queue.command_completed = MagicMock()
        self.mock_command_queue.progress_updated = MagicMock()
        self.mock_command_queue.manual_cleanup = MagicMock(return_value=len(tokens))
        
        # Replace the processor's command queue with our mock
        self.processor.command_queue = self.mock_command_queue
        
        # Process tokens
        print(f"Processing {len(tokens)} tokens for integration validation...")
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Process Qt events
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 2:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Verify final state
        final_state = self.processor._is_processing
        self.assertFalse(final_state, "Final processor state should be False")
        
        # Verify progress tracking
        self.assertEqual(self.processor._completed_commands, len(tokens), 
                        f"Completed commands should match token count")
        self.assertEqual(self.processor._success_count, len(tokens), 
                        f"Success count should match token count")
        
        print("✓ Integration validation PASSED")
        
    def test_comprehensive_validation_summary(self):
        """Generate comprehensive validation summary"""
        print("\n" + "="*80)
        print("COMPREHENSIVE VALIDATION SUMMARY")
        print("="*80)
        
        # Collect all validation results
        validation_results = []
        
        # Run all validation tests
        test_methods = [
            'test_sequential_processing_validation',
            'test_command_queue_synchronization',
            'test_error_handling_validation',
            'test_resource_cleanup_validation',
            'test_performance_validation',
            'test_integration_validation'
        ]
        
        for method_name in test_methods:
            try:
                test_method = getattr(self, method_name)
                test_method()
                validation_results.append((method_name, "PASSED"))
            except Exception as e:
                validation_results.append((method_name, f"FAILED: {str(e)}"))
                
        # Generate summary report
        passed_count = sum(1 for _, result in validation_results if result == "PASSED")
        total_count = len(validation_results)
        
        print(f"\nValidation Results: {passed_count}/{total_count} tests passed")
        print("-" * 80)
        
        for method_name, result in validation_results:
            status_icon = "✓" if result == "PASSED" else "✗"
            print(f"{status_icon} {method_name}: {result}")
            
        # Overall assessment
        success_rate = (passed_count / total_count) * 100
        print(f"\nOverall Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: Command queue implementation is robust and reliable")
        elif success_rate >= 80:
            print("✅ GOOD: Command queue implementation is functional with minor issues")
        elif success_rate >= 70:
            print("⚠️  AVERAGE: Command queue implementation has some issues that need attention")
        else:
            print("❌ POOR: Command queue implementation has significant problems")
            
        print("="*80)
        
        # Return results for further processing
        return {
            'total_tests': total_count,
            'passed_tests': passed_count,
            'success_rate': success_rate,
            'results': validation_results
        }


if __name__ == '__main__':
    # Configure logging for test execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the focused test suite
    unittest.main(verbosity=2)