import sys
import os

# Suppress QFileSystemWatcher warnings
os.environ["QT_LOGGING_RULES"] = "qt.core.filesystemwatcher=false"

from gui import LogReportGUI
from PyQt5.QtWidgets import QApplication

def cli_main(input_path, output_file):
    from processor import LogProcessor
    from generator import ReportGenerator
    
    print(f"Starting LOGReport processing")
    logs = LogProcessor().process_directory(input_path)
    ReportGenerator().generate_report(logs, output_file)
    print(f"Successfully created: {output_file}")

if __name__ == "__main__":
    # Default to GUI mode with no arguments or with --gui flag
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == "--gui"):
        app = QApplication(sys.argv)
        
        # Use centralized BsTool path resolver for consistent behavior
        from commander.utils.bstool_path_resolver import get_bstool_path
        bstool_path = get_bstool_path()
        
        if not bstool_path:
            print("WARNING: BsTool.exe not found. BsTool functionality will be disabled.")
            print("Please ensure BsTool.exe is in the correct location.")

        window = LogReportGUI(bstool_path=bstool_path)
        window.show()
        sys.exit(app.exec_())
    elif len(sys.argv) == 3:
        cli_main(sys.argv[1], sys.argv[2])
    else:
        print("Usage:")
        print("  GUI Mode: python main.py [--gui]  (--gui optional for GUI mode)")
        print("  CLI Mode: python main.py <input_dir> <output.pdf>")
        sys.exit(1)