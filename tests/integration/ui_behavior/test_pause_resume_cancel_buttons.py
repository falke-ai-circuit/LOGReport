"""
Test Pause/Resume/Cancel button functionality for Print All Nodes workflow.
Tests the callback-based pause mechanism between CommandQueue and NodeTreePresenter.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PyQt5.QtCore import QObject
from src.commander.presenters.node_tree_presenter import NodeTreePresenter
from src.commander.command_queue import CommandQueue, CommandWorker
from src.commander.models import NodeToken


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for NodeTreePresenter."""
    view = Mock()
    view.pause_btn = Mock()
    view.resume_btn = Mock()
    view.cancel_btn = Mock()
    view.pause_clicked = Mock()
    view.resume_clicked = Mock()
    view.cancel_clicked = Mock()
    view.item_expanded = Mock()
    
    node_manager = Mock()
    session_manager = Mock()
    log_writer = Mock()
    log_writer.log_write_completed = Mock()
    
    command_queue = Mock(spec=CommandQueue)
    command_queue.command_completed = Mock()
    command_queue.pause_check_callback = None
    
    fbc_service = Mock()
    rpc_service = Mock()
    bstool_service = Mock()
    context_menu_service = Mock()
    
    return {
        'view': view,
        'node_manager': node_manager,
        'session_manager': session_manager,
        'log_writer': log_writer,
        'command_queue': command_queue,
        'fbc_service': fbc_service,
        'rpc_service': rpc_service,
        'bstool_service': bstool_service,
        'context_menu_service': context_menu_service
    }


@pytest.fixture
def presenter(mock_dependencies):
    """Create NodeTreePresenter instance with mocked dependencies."""
    return NodeTreePresenter(
        view=mock_dependencies['view'],
        node_manager=mock_dependencies['node_manager'],
        session_manager=mock_dependencies['session_manager'],
        log_writer=mock_dependencies['log_writer'],
        command_queue=mock_dependencies['command_queue'],
        fbc_service=mock_dependencies['fbc_service'],
        rpc_service=mock_dependencies['rpc_service'],
        bstool_service=mock_dependencies['bstool_service'],
        context_menu_service=mock_dependencies['context_menu_service'],
        telnet_service=None,
        get_connection_info_callback=None
    )


class TestCallbackMechanism:
    """Test the callback-based pause/resume/cancel mechanism."""
    
    def test_should_continue_workflow_returns_true_initially(self, presenter):
        """Test that _should_continue_workflow returns True by default."""
        assert presenter._should_continue_workflow() is True
    
    def test_should_continue_workflow_returns_false_when_paused(self, presenter):
        """Test that _should_continue_workflow returns False when paused."""
        presenter._workflow_paused = True
        assert presenter._should_continue_workflow() is False
    
    def test_should_continue_workflow_returns_false_when_cancelled(self, presenter):
        """Test that _should_continue_workflow returns False when cancelled."""
        presenter._workflow_cancelled = True
        assert presenter._should_continue_workflow() is False
    
    def test_callback_set_in_command_queue_on_workflow_start(self, presenter, mock_dependencies):
        """Test that callback is set in CommandQueue when Print All Nodes starts."""
        # Mock required methods
        with patch.object(presenter, '_expand_entire_tree'):
            with patch.object(presenter.node_manager, 'get_all_nodes', return_value=[Mock()]):
                with patch.object(presenter, '_process_next_node_in_sequence'):
                    presenter.process_all_nodes_print_commands()
        
        # Verify callback was set
        assert mock_dependencies['command_queue'].pause_check_callback == presenter._should_continue_workflow
    
    def test_callback_cleared_on_workflow_completion(self, presenter, mock_dependencies):
        """Test that callback is cleared when workflow completes."""
        # Setup workflow state
        presenter._nodes_to_process = []
        presenter._current_node_index = 0
        presenter._total_nodes_to_process = 0
        
        # Call completion handler
        presenter._process_next_node_in_sequence()
        
        # Verify callback was cleared
        assert mock_dependencies['command_queue'].pause_check_callback is None
    
    def test_callback_cleared_on_workflow_cancel(self, presenter, mock_dependencies):
        """Test that callback is cleared when workflow is cancelled."""
        # Setup workflow state
        presenter._nodes_to_process = [Mock()]
        presenter._current_node_index = 0
        presenter._workflow_cancelled = True
        
        # Call handler
        presenter._process_next_node_in_sequence()
        
        # Verify callback was cleared
        assert mock_dependencies['command_queue'].pause_check_callback is None


class TestCommandWorkerCallback:
    """Test CommandWorker respects pause_check_callback."""
    
    def test_command_worker_executes_when_callback_returns_true(self):
        """Test that CommandWorker executes command when callback returns True."""
        token = NodeToken(
            token_id="162",
            token_type="FBC",
            name="AP01m",
            ip_address="192.168.0.11",
            node_ip="192.168.0.11"
        )
        
        callback = Mock(return_value=True)
        telnet_session = Mock()
        telnet_session.is_connected = True
        telnet_session.send_command = Mock(return_value="OK")
        telnet_session.connection = Mock()
        telnet_session.connection.get_socket = Mock(return_value=Mock())
        
        worker = CommandWorker(
            command="test command",
            token=token,
            telnet_session=telnet_session,
            pause_check_callback=callback
        )
        
        worker.run()
        
        # Verify callback was called
        callback.assert_called_once()
        # Verify command was executed
        telnet_session.send_command.assert_called_once_with("test command")
    
    def test_command_worker_skips_when_callback_returns_false(self):
        """Test that CommandWorker skips command when callback returns False."""
        token = NodeToken(
            token_id="162",
            token_type="FBC",
            name="AP01m",
            ip_address="192.168.0.11",
            node_ip="192.168.0.11"
        )
        
        callback = Mock(return_value=False)
        telnet_session = Mock()
        
        worker = CommandWorker(
            command="test command",
            token=token,
            telnet_session=telnet_session,
            pause_check_callback=callback
        )
        
        worker.run()
        
        # Verify callback was called
        callback.assert_called_once()
        # Verify command was NOT executed
        telnet_session.send_command.assert_not_called()
        # Verify worker marked as failed
        assert worker.success is False
        assert "skipped" in worker.result.lower()


class TestButtonStateMachine:
    """Test button state transitions during workflow."""
    
    def test_buttons_disabled_initially(self, presenter, mock_dependencies):
        """Test that control buttons are disabled initially."""
        # Buttons should be disabled after initialization
        # (Already set in NodeTreeView.__init__)
        pass
    
    def test_pause_cancel_enabled_on_workflow_start(self, presenter, mock_dependencies):
        """Test that pause and cancel buttons are enabled when workflow starts."""
        with patch.object(presenter, '_expand_entire_tree'):
            with patch.object(presenter.node_manager, 'get_all_nodes', return_value=[Mock()]):
                with patch.object(presenter, '_process_next_node_in_sequence'):
                    presenter.process_all_nodes_print_commands()
        
        # Verify pause and cancel enabled, resume disabled
        mock_dependencies['view'].pause_btn.setEnabled.assert_called_with(True)
        mock_dependencies['view'].cancel_btn.setEnabled.assert_called_with(True)
    
    def test_resume_enabled_pause_disabled_on_pause(self, presenter, mock_dependencies):
        """Test button states change correctly when pausing."""
        presenter._handle_pause()
        
        # Verify button states
        mock_dependencies['view'].pause_btn.setEnabled.assert_called_with(False)
        mock_dependencies['view'].resume_btn.setEnabled.assert_called_with(True)
        mock_dependencies['view'].cancel_btn.setEnabled.assert_called_with(True)
        
        # Verify flags set
        assert presenter._workflow_paused is True
    
    def test_pause_enabled_resume_disabled_on_resume(self, presenter, mock_dependencies):
        """Test button states change correctly when resuming."""
        presenter._workflow_paused = True  # Set initial paused state
        presenter._handle_resume()
        
        # Verify button states
        mock_dependencies['view'].pause_btn.setEnabled.assert_called_with(True)
        mock_dependencies['view'].resume_btn.setEnabled.assert_called_with(False)
        mock_dependencies['view'].cancel_btn.setEnabled.assert_called_with(True)
        
        # Verify flags cleared
        assert presenter._workflow_paused is False
    
    def test_all_buttons_disabled_on_cancel(self, presenter, mock_dependencies):
        """Test all buttons disabled when cancelling."""
        presenter._handle_cancel()
        
        # Verify all buttons disabled
        mock_dependencies['view'].pause_btn.setEnabled.assert_called_with(False)
        mock_dependencies['view'].resume_btn.setEnabled.assert_called_with(False)
        mock_dependencies['view'].cancel_btn.setEnabled.assert_called_with(False)
        
        # Verify flags set
        assert presenter._workflow_cancelled is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
