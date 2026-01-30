import os
import pty
import select
import subprocess
import time
import threading
from typing import Optional, Tuple

class InteractiveShell:
    """
    A robust interactive shell wrapper using Python's pty module.
    
    This solves the "deadlock" problem where agents hang on interactive commands 
    (like 'vim', 'nano', 'ssh', or scripts waiting for input).
    
    Architecture (Agent Zero Pattern):
    - Creates a Master/Slave PTY pair.
    - Runs the shell (zsh/bash) connected to the Slave PTY.
    - Reads from Master PTY (non-blocking) to get output.
    - Writes to Master PTY to send input/signals.
    """
    
    def __init__(self, shell_cmd: str = "/bin/zsh"):
        self.shell_cmd = shell_cmd
        self.master_fd: Optional[int] = None
        self.process: Optional[subprocess.Popen] = None
        self.running = False
        self._buffer = b""
        self._lock = threading.Lock()
        
    def start(self):
        """Start the interactive shell session."""
        if self.running:
            return
            
        # Create PTY pair
        self.master_fd, slave_fd = pty.openpty()
        
        # Start subprocess attached to slave PTY
        self.process = subprocess.Popen(
            [self.shell_cmd],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            preexec_fn=os.setsid, # Create new session/process group
            close_fds=True,
            shell=False 
            # Note: shell=False is safer, we launch the shell binary directly
        )
        
        # Close slave fd in parent (child has it now)
        os.close(slave_fd)
        
        self.running = True
        
        # Start a background reader thread to drain the PTY buffer
        # This prevents the PTY from filling up and blocking the child process
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()
        
        print(f"🐚 Interactive Shell ({self.shell_cmd}) started. PID: {self.process.pid}")

    def _reader_loop(self):
        """Continuously reads from master_fd and appends to buffer."""
        while self.running and self.process and self.process.poll() is None:
            try:
                # Use select to check if data is available to read (timeout 0.1s)
                r, w, x = select.select([self.master_fd], [], [], 0.1)
                if self.master_fd in r:
                    data = os.read(self.master_fd, 1024)
                    if not data:
                        break # EOF
                    with self._lock:
                        self._buffer += data
            except OSError:
                break
            except Exception as e:
                print(f"Shell reader error: {e}")
                break

    def read_output(self, timeout_ms: int = 1000, clear_buffer: bool = True) -> str:
        """
        Read accumulated output from the shell.
        
        Args:
            timeout_ms: How long to wait for NEW output if buffer is empty
            clear_buffer: Whether to clear the read buffer after returning (default: True)
        """
        if not self.running:
            return "Shell is not running."
            
        # Wait a bit if buffer is empty, to capture immediate command response
        if not self._buffer:
            time.sleep(timeout_ms / 1000.0)
            
        with self._lock:
            # Decode with replacement to handle binary/emoji data safely
            try:
                output = self._buffer.decode('utf-8', errors='replace')
            except:
                output = str(self._buffer)
                
            if clear_buffer:
                self._buffer = b""
                
        return output

    def send_input(self, text: str, append_newline: bool = True):
        """Send text input to the shell."""
        if not self.running or self.master_fd is None:
            raise RuntimeError("Shell is not running")
            
        if append_newline and not text.endswith('\n'):
            text += '\n'
            
        os.write(self.master_fd, text.encode('utf-8'))

    def send_interrupt(self):
        """Send Ctrl+C (SIGINT) to the shell."""
        if self.running and self.master_fd is not None:
             # ASCII 3 is ETX (End of Text), commonly Ctrl+C
             os.write(self.master_fd, b'\x03')

    def execute_command(self, command: str, timeout_seconds: int = 10) -> str:
        """
        High-level wrapper to:
        1. Send command
        2. Wait for output (or timeout)
        3. Return result
        """
        if not self.running:
            self.start()
            
        # Clear previous buffer junk
        self.read_output(timeout_ms=10) 
        
        self.send_input(command)
        
        # Accumulate output until silent or timeout
        # Simple heuristic: wait for output, then wait for silence
        start_time = time.time()
        final_output = ""
        
        while (time.time() - start_time) < timeout_seconds:
            chunk = self.read_output(timeout_ms=500, clear_buffer=True)
            if chunk:
                final_output += chunk
                # Reset timeout if we are still getting data? 
                # Ideally yes, but for now strict timeout prevents hangs
            else:
                # No data for 500ms... assumes command finished? 
                # This is tricky in async shells, but good enough for v1
                if final_output.strip(): 
                    break 
                    
        return final_output

    def close(self):
        """Terminate the shell."""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait()
        if self.master_fd:
            os.close(self.master_fd)

if __name__ == "__main__":
    # Test
    shell = InteractiveShell()
    shell.start()
    
    print("\n--- Test ls ---")
    print(shell.execute_command("ls -la"))
    
    print("\n--- Test PWD ---")
    print(shell.execute_command("pwd"))
    
    print("\n--- Test Python Interactive ---")
    shell.send_input("python3")
    print(shell.read_output(2000))
    
    shell.send_input("print(10 + 10)")
    print(shell.read_output(1000))
    
    shell.send_input("exit()")
    print(shell.read_output(1000))

    shell.close()
