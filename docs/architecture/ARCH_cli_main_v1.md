# CLI Main Function Architecture

## Overview
The `cli_main` function (`src/main.py`) serves as the primary command-line interface entry point for the LOGReport application. It orchestrates the processing of log files and the generation of reports based on user-provided input and output paths.

## Function Signature
`cli_main(input_path, output_file)`

## Parameters
- `input_path` (str): The directory containing log files to be processed. Supported file extensions include `.log`, `.txt`, and `.text`.
- `output_file` (str): The full path, including filename, where the generated report will be saved.

## Core Functionality
1. **Initialization Message**: Prints a message indicating the start of the LOGReport processing.
2. **Log Processing**: Utilizes an instance of `LogProcessor` to:
    - Scan the `input_path` directory for relevant log files.
    - Read and parse the content of these log files.
    - Return a list of dictionaries, each representing a processed log file with its extracted details.
3. **Report Generation**: Employs an instance of `ReportGenerator` to:
    - Take the processed log data as input.
    - Generate a comprehensive report based on the data.
    - Save the generated report to the specified `output_file`.
4. **Completion Message**: Prints a confirmation message upon successful report generation, including the path to the generated file.

## Dependencies
- `LogProcessor` (from `processor.py`): Used for scanning directories and processing log files.
- `ReportGenerator` (from `generator.py`): Used for generating reports from processed log data.

## Usage Example
```python
# Example of how cli_main is typically invoked
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        cli_main(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python main.py <input_directory> <output_report_file>")