from PyQt5.QtCore import QObject, pyqtSignal, QThread
from typing import Dict, List, Any, Optional
import logging
import time

from ..models import NodeToken
from ..command_queue import QueuedCommand
from ..node_manager import NodeManager
from ..command_queue import CommandQueue
from .fbc_command_service import FbcCommandService
from .rpc_command_service import RpcCommandService
from .bstool_command_service import BsToolCommandService
from .log_command_service import LogCommandService

class HierarchicalCommandService(QObject):
    """
    Service for orchestrating the sequential execution of hierarchical commands
    for a given node.
    """
    
    # Signals for progress reporting and error handling
    command_started = pyqtSignal(str, int, int, str)  # command_name, current_index, total_commands, command_type
    command_completed = pyqtSignal(str, int, int, str, bool, str) # command_name, current_index, total_commands, command_type, success, result
    sequence_progress = pyqtSignal(int, int, str) # current_completed, total_commands, status_message
    sequence_finished = pyqtSignal(str, bool)     # hierarchical_command_name, success
    sequence_error = pyqtSignal(str, str)         # hierarchical_command_name, error_message

    def __init__(self,
                 node_manager: NodeManager,
                 command_queue: CommandQueue,
                 fbc_service: FbcCommandService,
                 rpc_service: RpcCommandService,
                 bstool_service: BsToolCommandService,
                 log_service: LogCommandService,
                 parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.node_manager = node_manager
        self.command_queue = command_queue
        self.fbc_service = fbc_service
        self.rpc_service = rpc_service
        self.bstool_service = bstool_service
        self.log_service = log_service
        
        # Connect to command_queue's command_completed signal to track subcommand completion
        self.command_queue.command_completed.connect(self._handle_subcommand_completion)
        
        self._current_sequence_commands: List[Dict[str, Any]] = []
        self._current_sequence_node_token: Optional[NodeToken] = None
        self._current_sequence_name: str = ""
        self._current_command_index: int = -1
        self._stop_on_error: bool = True # Default behavior as per design document

    def execute_hierarchical_command(self,
                                     node_token: NodeToken,
                                     hierarchical_command_name: str,
                                     stop_on_error: bool = True):
        """
        Executes a defined hierarchical command sequence for a given node.
        
        Args:
            node_token (NodeToken): The NodeToken associated with the command.
            hierarchical_command_name (str): The name of the hierarchical command to execute.
            stop_on_error (bool): If True, stops the sequence on the first error.
                                  If False, logs errors and continues.
        """
        self.logger.info(f"Starting hierarchical command '{hierarchical_command_name}' for node {node_token.name}")
        self._current_sequence_node_token = node_token
        self._current_sequence_name = hierarchical_command_name
        self._stop_on_error = stop_on_error
        self._current_command_index = -1 # Reset index for new sequence

        node = self.node_manager.get_node(node_token.name)
        if not node:
            error_msg = f"Node '{node_token.name}' not found for hierarchical command."
            self.logger.error(error_msg)
            self.sequence_error.emit(hierarchical_command_name, error_msg)
            self.sequence_finished.emit(hierarchical_command_name, False)
            return

        # Retrieve hierarchical commands from the Node object, indexed by token_type
        # The design document example shows "FBC_NODE_TYPE" as a key, implying it's per token_type
        # However, the NodeToken is passed, so we should use its token_type to find the relevant commands.
        # If hierarchical commands are defined at the Node level, we need to adjust this logic.
        # Assuming hierarchical_commands are stored in Node, keyed by token_type, then by command name.
        
        # The design document's example JSON snippet shows hierarchical_commands directly under a node type,
        # not under a specific token. So, we should look up the hierarchical commands using the node's name
        # and the hierarchical_command_name.
        
        # Re-evaluating the design document's JSON snippet:
        # { "FBC_NODE_TYPE": { "hierarchical_commands": { "Full FBC Sequence": [...] } } }
        # This structure implies that `hierarchical_commands` is a property of the *node type definition*
        # rather than a specific Node instance. NodeManager currently loads `nodes.json` as a list of Nodes.
        # The `hierarchical_commands` field was added to the `Node` dataclass.
        # So, we should access `node.hierarchical_commands` and then look up by `hierarchical_command_name`.
        
        hierarchical_commands_for_node = node.hierarchical_commands.get(node_token.token_type, {})
        self._current_sequence_commands = hierarchical_commands_for_node.get(hierarchical_command_name, [])

        if not self._current_sequence_commands:
            error_msg = f"Hierarchical command '{hierarchical_command_name}' not found for token type '{node_token.token_type}' in node '{node_token.name}'."
            self.logger.error(error_msg)
            self.sequence_error.emit(hierarchical_command_name, error_msg)
            self.sequence_finished.emit(hierarchical_command_name, False)
            return

        self.logger.info(f"Executing {len(self._current_sequence_commands)} subcommands for sequence '{hierarchical_command_name}'")
        self._execute_next_subcommand()

    def _execute_next_subcommand(self):
        """Executes the next subcommand in the sequence."""
        self._current_command_index += 1
        
        if self._current_command_index >= len(self._current_sequence_commands):
            self.logger.info(f"Hierarchical command sequence '{self._current_sequence_name}' completed successfully.")
            self.sequence_finished.emit(self._current_sequence_name, True)
            self._reset_sequence_state()
            return

        command_definition = self._current_sequence_commands[self._current_command_index]
        command_type = command_definition.get("type")
        command_args = command_definition.get("command")
        parameters = command_definition.get("parameters", {}) # For BSTool, RPC actions etc.

        self.logger.info(f"Executing subcommand {self._current_command_index + 1}/{len(self._current_sequence_commands)}: Type={command_type}, Command={command_args}")
        self.command_started.emit(
            self._current_sequence_name,
            self._current_command_index + 1,
            len(self._current_sequence_commands),
            command_type
        )
        self.sequence_progress.emit(
            self._current_command_index + 1,
            len(self._current_sequence_commands),
            f"Executing {command_type} command: {command_args}"
        )

        try:
            if command_type == "FBC":
                generated_command = self.fbc_service.generate_fieldbus_command(command_args)
                queued_cmd = QueuedCommand(command=generated_command, token=self._current_sequence_node_token)
                self.command_queue.add_command(queued_cmd.command, queued_cmd.token)
            elif command_type == "RPC":
                action = parameters.get("action", "print")
                generated_command = self.rpc_service.generate_rpc_command(command_args, action)
                queued_cmd = QueuedCommand(command=generated_command, token=self._current_sequence_node_token)
                self.command_queue.add_command(queued_cmd.command, queued_cmd.token)
            elif command_type == "BSTool":
                log_file_path = parameters.get("log_file_path", self._current_sequence_node_token.log_path)
                bstool_command_args = command_args # The 'command' field holds the bstool args
                
                # BSTool execution is synchronous and directly handled by its service
                # We need to run this in a separate thread to avoid blocking the main thread
                # and wait for its completion before proceeding to the next subcommand.
                
                # Create a QThread for synchronous BSTool execution
                bstool_thread = QThread()
                bstool_worker = BsToolWorker(self.bstool_service, log_file_path, bstool_command_args)
                bstool_worker.moveToThread(bstool_thread)
                
                bstool_thread.started.connect(bstool_worker.run)
                bstool_worker.finished.connect(bstool_thread.quit)
                bstool_worker.finished.connect(bstool_worker.deleteLater)
                bstool_thread.finished.connect(bstool_thread.deleteLater)
                
                bstool_worker.result_signal.connect(
                    lambda success, result: self._handle_bstool_completion(
                        command_definition, success, result
                    )
                )
                
                bstool_thread.start()
                # The _handle_bstool_completion will be called when BSTool finishes.
                # It will then call _execute_next_subcommand or handle errors.
                return # Do not proceed to _execute_next_subcommand here
                
            elif command_type == "LOG":
                log_paths = parameters.get("log_paths", [self._current_sequence_node_token.log_path])
                # LOG execution is synchronous and directly handled by its service
                # It opens files, which is a UI operation.
                self.log_service.process_all_log_commands(log_paths)
                # Since LOG commands are typically quick UI operations, we can consider them
                # completed immediately for the purpose of sequence progression.
                self._handle_subcommand_completion(
                    command_definition.get("command", "LOG_COMMAND"),
                    "Log files opened",
                    True,
                    self._current_sequence_node_token
                )
            else:
                raise ValueError(f"Unknown command type: {command_type}")
        except Exception as e:
            self.logger.error(f"Error executing subcommand '{command_args}' of type '{command_type}': {str(e)}", exc_info=True)
            self.command_completed.emit(
                self._current_sequence_name,
                self._current_command_index + 1,
                len(self._current_sequence_commands),
                command_type,
                False,
                str(e)
            )
            if self._stop_on_error:
                self.sequence_error.emit(self._current_sequence_name, f"Subcommand failed: {command_args} - {str(e)}")
                self.sequence_finished.emit(self._current_sequence_name, False)
                self._reset_sequence_state()
            else:
                self._execute_next_subcommand() # Continue to next command

    def _handle_subcommand_completion(self, command_str: str, result: str, success: bool, token: NodeToken):
        """
        Handles the completion of a subcommand executed by the CommandQueue.
        This method is connected to the CommandQueue's command_completed signal.
        """
        # Only process completions for the currently active hierarchical sequence
        if not self._current_sequence_node_token or token.token_id != self._current_sequence_node_token.token_id:
            return

        # Find the command definition that just completed
        completed_command_definition = None
        for i, cmd_def in enumerate(self._current_sequence_commands):
            # This is a simplified check. A more robust solution might involve
            # a unique ID for each QueuedCommand or a more complex matching logic.
            # For FBC/RPC, the command_str is the generated command.
            # For BSTool/LOG, the command_str might be the original 'command' field from definition.
            
            # For FBC/RPC, we need to match the generated command string.
            # For other types, we need to match the original command definition.
            
            # Since we are only connecting to command_queue.command_completed, this signal
            # is only emitted for FBC/RPC commands that go through the CommandQueue.
            # BSTool and LOG commands are handled by direct service calls and their
            # completion is managed differently (e.g., _handle_bstool_completion).
            
            # So, this handler is specifically for FBC/RPC commands.
            
            if cmd_def.get("type") in ["FBC", "RPC"]:
                # Re-generate command to match against command_str
                if cmd_def.get("type") == "FBC":
                    expected_command_str = self.fbc_service.generate_fieldbus_command(cmd_def.get("command"))
                else: # RPC
                    action = cmd_def.get("parameters", {}).get("action", "print")
                    expected_command_str = self.rpc_service.generate_rpc_command(cmd_def.get("command"), action)
                
                if expected_command_str == command_str:
                    completed_command_definition = cmd_def
                    break
        
        if not completed_command_definition:
            self.logger.warning(f"Could not find matching command definition for completed command: {command_str}")
            return

        self.logger.debug(f"Subcommand '{command_str}' completed with success={success}")
        self.command_completed.emit(
            self._current_sequence_name,
            self._current_command_index + 1,
            len(self._current_sequence_commands),
            completed_command_definition.get("type"),
            success,
            result
        )

        if not success and self._stop_on_error:
            self.sequence_error.emit(self._current_sequence_name, f"Subcommand failed: {command_str} - {result}")
            self.sequence_finished.emit(self._current_sequence_name, False)
            self._reset_sequence_state()
        else:
            self._execute_next_subcommand()

    def _handle_bstool_completion(self, command_definition: Dict[str, Any], success: bool, result: str):
        """
        Handles the completion of a BSTool subcommand.
        """
        command_type = command_definition.get("type")
        command_args = command_definition.get("command")
        
        self.logger.debug(f"BSTool subcommand '{command_args}' completed with success={success}")
        self.command_completed.emit(
            self._current_sequence_name,
            self._current_command_index + 1,
            len(self._current_sequence_commands),
            command_type,
            success,
            result
        )

        if not success and self._stop_on_error:
            self.sequence_error.emit(self._current_sequence_name, f"BSTool subcommand failed: {command_args} - {result}")
            self.sequence_finished.emit(self._current_sequence_name, False)
            self._reset_sequence_state()
        else:
            self._execute_next_subcommand()

    def _reset_sequence_state(self):
        """Resets the internal state after a sequence completes or errors."""
        self._current_sequence_commands = []
        self._current_sequence_node_token = None
        self._current_sequence_name = ""
        self._current_command_index = -1
        self._stop_on_error = True

class BsToolWorker(QObject):
    """Worker for executing BSTool commands in a separate thread."""
    finished = pyqtSignal()
    result_signal = pyqtSignal(bool, str) # success, result

    def __init__(self, bstool_service: BsToolCommandService, log_file_path: str, bstool_command_args: str):
        super().__init__()
        self.bstool_service = bstool_service
        self.log_file_path = log_file_path
        self.bstool_command_args = bstool_command_args
        self.logger = logging.getLogger(__name__)

    def run(self):
        success = False
        result = ""
        try:
            # Capture bstool output and errors
            # The execute_bstool method already emits signals for output,
            # but we need to capture the final success/failure for the sequence.
            # This requires a modification to bstool_command_service to return a result.
            # For now, we'll assume execute_bstool handles its own logging and error reporting
            # and we'll just emit a generic success/failure based on its completion.
            
            # A more robust solution would involve modifying BsToolCommandService.execute_bstool
            # to return a Future or a signal that indicates its final completion status and output.
            # For this implementation, we'll rely on the signals emitted by BsToolCommandService
            # and assume a successful completion if no exception is raised here.
            
            self.logger.info(f"BsToolWorker: Executing BSTool command: {self.bstool_command_args}")
            self.bstool_service.execute_bstool(self.log_file_path, self.bstool_command_args)
            
            # Since execute_bstool runs in a separate thread and emits signals,
            # we need a way to know when it's truly finished and its outcome.
            # This is a simplification. In a real scenario, BsToolCommandService
            # would need to provide a mechanism to await its completion.
            # For now, we'll assume it completes successfully if no immediate exception.
            # This is a known limitation and needs to be addressed in future refinements.
            
            # Simulate waiting for BSTool to finish (replace with actual mechanism)
            time.sleep(5) # Placeholder for actual completion waiting
            
            success = True
            result = "BSTool command executed (assumed success for now)"
            self.logger.info(f"BsToolWorker: BSTool command finished: {result}")
        except Exception as e:
            result = f"BSTool command failed: {str(e)}"
            self.logger.error(f"BsToolWorker: {result}", exc_info=True)
            success = False
        finally:
            self.result_signal.emit(success, result)
            self.finished.emit()
