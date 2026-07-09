"""
Direct test of BsTool.exe execution to diagnose the issue
"""
import subprocess
import os
import sys
import tempfile

def test_bstool_execution():
    """Test BsTool.exe execution with different approaches"""
    
    # Find BsTool.exe
    bstool_path = os.path.join(os.path.dirname(__file__), "BsTool.exe")
    print(f"BsTool.exe path: {bstool_path}")
    print(f"BsTool.exe exists: {os.path.exists(bstool_path)}")
    
    if not os.path.exists(bstool_path):
        print("ERROR: BsTool.exe not found!")
        return
    
    # Set environment
    env = os.environ.copy()
    env["COMMUNICATION_LINE"] = "AB01"
    
    print("\n" + "="*80)
    print("TEST 1: Direct execution with PIPE (current implementation)")
    print("="*80)
    try:
        proc = subprocess.Popen(
            [bstool_path],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"Process started, PID: {proc.pid}")
        
        # Try to send newline and close stdin
        try:
            proc.stdin.write('\n')
            proc.stdin.flush()
            proc.stdin.close()
            print("Sent newline to stdin and closed")
        except Exception as e:
            print(f"Error writing to stdin: {e}")
        
        # Wait with timeout
        try:
            stdout, stderr = proc.communicate(timeout=5)
            print(f"Return code: {proc.returncode}")
            print(f"STDOUT ({len(stdout)} chars):\n{stdout}")
            print(f"STDERR ({len(stderr)} chars):\n{stderr}")
        except subprocess.TimeoutExpired:
            print("Process timed out!")
            proc.kill()
            stdout, stderr = proc.communicate()
            print(f"STDOUT after kill:\n{stdout}")
            print(f"STDERR after kill:\n{stderr}")
    except Exception as e:
        print(f"Error in TEST 1: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("TEST 2: With temp files (like current code)")
    print("="*80)
    try:
        stdout_temp = tempfile.TemporaryFile(mode='w+', encoding='utf-8', errors='replace', delete=False)
        stderr_temp = tempfile.TemporaryFile(mode='w+', encoding='utf-8', errors='replace', delete=False)
        
        print(f"Temp stdout: {stdout_temp.name}")
        print(f"Temp stderr: {stderr_temp.name}")
        
        proc = subprocess.Popen(
            [bstool_path],
            env=env,
            stdin=subprocess.PIPE,
            stdout=stdout_temp,
            stderr=stderr_temp,
            text=True
        )
        
        print(f"Process started, PID: {proc.pid}")
        
        # Send newline
        try:
            proc.stdin.write('\n')
            proc.stdin.flush()
            proc.stdin.close()
            print("Sent newline to stdin and closed")
        except Exception as e:
            print(f"Error writing to stdin: {e}")
        
        # Wait
        try:
            proc.wait(timeout=5)
            print(f"Return code: {proc.returncode}")
        except subprocess.TimeoutExpired:
            print("Process timed out!")
            proc.kill()
            proc.wait()
        
        # Read files
        stdout_temp.seek(0)
        stderr_temp.seek(0)
        stdout_content = stdout_temp.read()
        stderr_content = stderr_temp.read()
        
        print(f"STDOUT ({len(stdout_content)} chars):\n{stdout_content}")
        print(f"STDERR ({len(stderr_content)} chars):\n{stderr_content}")
        
        # Cleanup
        stdout_temp.close()
        stderr_temp.close()
        os.unlink(stdout_temp.name)
        os.unlink(stderr_temp.name)
        
    except Exception as e:
        print(f"Error in TEST 2: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("TEST 3: Using subprocess.run with capture_output")
    print("="*80)
    try:
        result = subprocess.run(
            [bstool_path],
            env=env,
            input='\n',  # Send newline as input
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"Return code: {result.returncode}")
        print(f"STDOUT ({len(result.stdout)} chars):\n{result.stdout}")
        print(f"STDERR ({len(result.stderr)} chars):\n{result.stderr}")
    except subprocess.TimeoutExpired as e:
        print("Process timed out!")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
    except Exception as e:
        print(f"Error in TEST 3: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("TEST 4: Direct execution without input (might hang)")
    print("="*80)
    try:
        result = subprocess.run(
            [bstool_path],
            env=env,
            capture_output=True,
            text=True,
            timeout=3
        )
        print(f"Return code: {result.returncode}")
        print(f"STDOUT ({len(result.stdout)} chars):\n{result.stdout}")
        print(f"STDERR ({len(result.stderr)} chars):\n{result.stderr}")
    except subprocess.TimeoutExpired as e:
        print("Process timed out (expected if BsTool waits for input)!")
        print(f"STDOUT: {e.stdout if e.stdout else '(none)'}")
        print(f"STDERR: {e.stderr if e.stderr else '(none)'}")
    except Exception as e:
        print(f"Error in TEST 4: {e}")

if __name__ == "__main__":
    test_bstool_execution()
