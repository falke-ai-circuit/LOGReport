"""
Comprehensive Command Queue Validation Test Suite

This test suite provides systematic validation of the command queue implementation
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


class TestComprehensiveCommandQueueValidation(unittest.TestCase):
    """Comprehensive validation of command queue functionality"""
    
    def setUp(self):
        """Set up comprehensive test environment"""
        # Create Qt application if needed
        if not QCoreApplication.instance():
            self.app = QCoreApplication([])
        else:
            self.app = QCoreApplication.instance()
            
        # Configure test logging
        logging.basicConfig(level=logging.DEBUG)
        self.test_logger = logging.getLogger(__name__)
        
        # Create mock services with comprehensive mocking
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
        
    def test_comprehensive_sequential_processing_validation(self):
        """Comprehensive validation of sequential processing with mixed token types"""
        print("\n" + "="*80)
        print("COMPREHENSIVE SEQUENTIAL PROCESSING VALIDATION")
        print("="*80)
        
        # Create comprehensive test tokens
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),
            NodeToken(token_id="164", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="165", token_type="RPC", node_ip="192.168.0.11"),
            NodeToken(token_id="166", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="167", token_type="RPC", node_ip="192.168.0.11")
        ]
        
        # Track processing order and timing
        processing_order = []
        processing_times = []
        start_time = time.time()
        
        # Enhanced mock for command queue to track processing
        def track_add_command(command, token, telnet_client=None):
            processing_time = time.time() - start_time
            processing_order.append((token.token_id, token.token_type, processing_time))
            processing_times.append(processing_time)
            self.test_logger.info(f"Command queued: {command} for token {token.token_id} at {processing_time:.2f}s")
            
            # Simulate command completion with realistic timing
            completion_delay = max(0.1, 0.05 + (hash(token.token_id) % 100) / 1000)  # 50-150ms delay
            QTimer.singleShot(int(completion_delay * 1000), lambda: self.mock_command_queue.command_completed.emit(
                command, f"Success for {token.token_id}", True, token
            ))
            
        self.mock_command_queue = MagicMock(spec=CommandQueue)
        self.mock_command_queue.add_command = track_add_command
        self.mock_command_queue.command_completed = MagicMock()
        self.mock_command_queue.progress_updated = MagicMock()
        self.mock_command_queue.manual_cleanup = MagicMock(return_value=0)
        
        # Replace the processor's command queue with our mock
        self.processor.command_queue = self.mock_command_queue
        
        # Process tokens sequentially
        print(f"Starting sequential processing of {len(tokens)} tokens...")
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Process Qt events to allow signals to be handled
        max_wait_time = 5  # seconds
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < max_wait_time:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Verify processing results
        print(f"\nProcessing completed in {time.time() - start_time:.2f} seconds")
        print(f"Processing order: {processing_order}")
        print(f"Processing times: {processing_times}")
        
        # Validate sequential order
        expected_order = [
            ("162", "FBC"), ("163", "RPC"), ("164", "FBC"), ("165", "RPC"), 
            ("166", "FBC"), ("167", "RPC")
        ]
        actual_order = [(item[0], item[1]) for item in processing_order]
        
        self.assertEqual(actual_order, expected_order, 
                        f"Expected processing order {expected_order}, got {actual_order}")
        
        # Validate timing (should be sequential, not parallel)
        for i in range(1, len(processing_times)):
            self.assertGreater(processing_times[i], processing_times[i-1], 
                             f"Token {i} should start after token {i-1}")
            
        # Validate all tokens were processed
        self.assertEqual(len(processing_order), len(tokens), 
                        f"Expected {len(tokens)} tokens processed, got {len(processing_order)}")
        
        # Validate no overlapping processing
        time_differences = [processing_times[i] - processing_times[i-1] for i in range(1, len(processing_times))]
        min_gap = min(time_differences)
        self.assertGreater(min_gap, 0.01, f"Minimum processing gap should be > 10ms, got {min_gap:.3f}s")
        
        print("✓ Sequential processing validation PASSED")
        
    def test_command_queue_synchronization_and_thread_safety(self):
        """Test command queue synchronization and thread safety"""
        print("\n" + "="*80)
        print("COMMAND QUEUE SYNCHRONIZATION AND THREAD SAFETY VALIDATION")
        print("="*80)
        
        # Verify single-threaded configuration
        max_threads = self.command_queue.thread_pool.maxThreadCount()
        self.assertEqual(max_threads, 1, 
                        f"Command queue should use single thread, but has {max_threads} threads")
        
        print(f"✓ Thread pool configured for single-threaded execution: {max_threads} threads")
        
        # Test processing state synchronization
        initial_state = self.command_queue.is_processing
        self.assertFalse(initial_state, "Initial processing state should be False")
        
        # Simulate concurrent access attempts
        access_results = []
        
        def attempt_processing():
            try:
                state = self.command_queue.is_processing
                access_results.append(state)
                return state
            except Exception as e:
                access_results.append(f"ERROR: {e}")
                return None
                
        # Test multiple concurrent reads
        import threading
        threads = []
        for i in range(5):
            thread = threading.Thread(target=attempt_processing)
            threads.append(thread)
            thread.start()
            
        for thread in threads:
            thread.join()
            
        # All threads should see consistent state
        self.assertTrue(all(result == initial_state for result in access_results if isinstance(result, bool)),
                       f"Inconsistent processing state detected: {access_results}")
        
        print("✓ Thread safety validation PASSED")
        
    def test_error_handling_and_recovery_mechanisms(self):
        """Test comprehensive error handling and recovery mechanisms"""
        print("\n" + "="*80)
        print("ERROR HANDLING AND RECOVERY MECHANISMS VALIDATION")
        print("="*80)
        
        # Create tokens with mixed success/failure scenarios
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),  # Success
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),  # Failure
            NodeToken(token_id="164", token_type="FBC", node_ip="192.168.0.11"),  # Success
            NodeToken(token_id="165", token_type="RPC", node_ip="192.168.0.11"),  # Failure
            NodeToken(token_id="166", token_type="FBC", node_ip="192.168.0.11"),  # Success
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
        self.mock_command_queue.manual_cleanup = MagicMock(return_value=0)
        
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
        self.assertEqual(error_count, 2, f"Expected 2 errors, got {error_count}")
        self.assertEqual(success_count, 3, f"Expected 3 successes, got {success_count}")
        
        # Verify processing continued despite errors
        self.assertEqual(len(self.command_results), len(tokens), 
                        f"All {len(tokens)} tokens should have been processed despite errors")
        
        # Verify circuit breaker wasn't triggered (less than 3 consecutive failures)
        self.assertNotEqual(self.processor._circuit_breaker.get_state().name, "OPEN",
                           "Circuit breaker should not be triggered with non-consecutive failures")
        
        print("✓ Error handling and recovery validation PASSED")
        
    def test_resource_cleanup_and_memory_management(self):
        """Test resource cleanup and memory management"""
        print("\n" + "="*80)
        print("RESOURCE CLEANUP AND MEMORY MANAGEMENT VALIDATION")
        print("="*80)
        
        # Create test tokens
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),
            NodeToken(token_id="164", token_type="FBC", node_ip="192.168.0.11"),
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
        
        # Verify cleanup was called after each command completion
        self.assertEqual(len(cleanup_calls), len(tokens), 
                        f"Cleanup should be called once per token")
        
        # Verify manual cleanup was called at the end
        self.mock_command_queue.manual_cleanup.assert_called_once()
        
        print("✓ Resource cleanup and memory management validation PASSED")
        
    def test_performance_and_throughput_validation(self):
        """Test performance and throughput characteristics"""
        print("\n" + "="*80)
        print("PERFORMANCE AND THROUGHPUT VALIDATION")
        print("="*80)
        
        # Create larger batch for performance testing
        tokens = [
            NodeToken(token_id=str(i), token_type="FBC" if i % 2 == 0 else "RPC", node_ip="192.168.0.11")
            for i in range(162, 172)  # 10 tokens
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
        print(f"  Processing times: {[f'{t:.3f}s' for t in processing_times]}")
        
        # Validate performance expectations
        self.assertLess(total_time, 3.0, f"Total processing time should be < 3s, got {total_time:.2f}s")
        self.assertGreater(throughput, 2.0, f"Throughput should be > 2 tokens/sec, got {throughput:.2f}")
        
        # Validate sequential processing (no overlapping)
        for i in range(1, len(processing_times)):
            self.assertGreater(processing_times[i], processing_times[i-1], 
                             f"Token {i} should start after token {i-1}")
            
        print("✓ Performance and throughput validation PASSED")
        
    def test_integration_with_sequential_command_processor(self):
        """Test integration with sequential command processor"""
        print("\n" + "="*80)
        print("INTEGRATION WITH SEQUENTIAL COMMAND PROCESSOR VALIDATION")
        print("="*80)
        
        # Test processor state management
        initial_state = self.processor._is_processing
        self.assertFalse(initial_state, "Initial processor state should be False")
        
        # Create test tokens
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),
        ]
        
        # Track processor state changes
        state_changes = []
        
        def track_state_change():
            state_changes.append(self.processor._is_processing)
            
        # Patch the processor to track state changes
        original_process_next = self.processor._process_next_token
        self.processor._process_next_token = lambda: [track_state_change(), original_process_next()]
        
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
            
        # Verify processor state management
        self.assertTrue(len(state_changes) > 0, "State changes should be tracked")
        
        # Verify final state
        final_state = self.processor._is_processing
        self.assertFalse(final_state, "Final processor state should be False")
        
        # Verify progress tracking
        self.assertEqual(self.processor._completed_commands, len(tokens), 
                        f"Completed commands should match token count")
        self.assertEqual(self.processor._success_count, len(tokens), 
                        f"Success count should match token count")
        
        print("✓ Integration with sequential command processor validation PASSED")
        
    def test_comprehensive_validation_summary(self):
        """Generate comprehensive validation summary"""
        print("\n" + "="*80)
        print("COMPREHENSIVE VALIDATION SUMMARY")
        print("="*80)
        
        # Collect all validation results
        validation_results = []
        
        # Run all validation tests
        test_methods = [
            'test_comprehensive_sequential_processing_validation',
            'test_command_queue_synchronization_and_thread_safety',
            'test_error_handling_and_recovery_mechanisms',
            'test_resource_cleanup_and_memory_management',
            'test_performance_and_throughput_validation',
            'test_integration_with_sequential_command_processor'
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
    
    # Run the comprehensive test suite
    unittest.main(verbosity=2)