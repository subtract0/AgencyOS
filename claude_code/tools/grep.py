from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Optional, Literal
import subprocess
import os
import shlex

class Grep(BaseTool):
    """
    A powerful search tool built on ripgrep.
    
    Usage:
    - ALWAYS use Grep for search tasks. NEVER invoke `grep` or `rg` as a Bash command
    - Supports full regex syntax (e.g., "log.*Error", "function\\s+\\w+")
    - Filter files with glob parameter (e.g., "*.js", "**/*.tsx") or type parameter
    - Output modes: "content" shows matching lines, "files_with_matches" shows only file paths, "count" shows match counts
    - Pattern syntax: Uses ripgrep (not grep) - literal braces need escaping
    - Multiline matching: By default patterns match within single lines only
    """
    
    pattern: str = Field(..., description="The regular expression pattern to search for in file contents")
    path: Optional[str] = Field(None, description="File or directory to search in (rg PATH). Defaults to current working directory.")
    glob: Optional[str] = Field(None, description="Glob pattern to filter files (e.g. '*.js', '*.{ts,tsx}') - maps to rg --glob")
    output_mode: Optional[Literal["content", "files_with_matches", "count"]] = Field("files_with_matches", description="Output mode: 'content' shows matching lines (supports -A/-B/-C context, -n line numbers, head_limit), 'files_with_matches' shows file paths (supports head_limit), 'count' shows match counts (supports head_limit). Defaults to 'files_with_matches'.")
    B: Optional[int] = Field(None, description="Number of lines to show before each match (rg -B). Requires output_mode: 'content', ignored otherwise.", alias="-B")
    A: Optional[int] = Field(None, description="Number of lines to show after each match (rg -A). Requires output_mode: 'content', ignored otherwise.", alias="-A") 
    C: Optional[int] = Field(None, description="Number of lines to show before and after each match (rg -C). Requires output_mode: 'content', ignored otherwise.", alias="-C")
    n: Optional[bool] = Field(None, description="Show line numbers in output (rg -n). Requires output_mode: 'content', ignored otherwise.", alias="-n")
    i: Optional[bool] = Field(None, description="Case insensitive search (rg -i)", alias="-i")
    type: Optional[str] = Field(None, description="File type to search (rg --type). Common types: js, py, rust, go, java, etc. More efficient than include for standard file types.")
    head_limit: Optional[int] = Field(None, description="Limit output to first N lines/entries, equivalent to '| head -N'. Works across all output modes: content (limits output lines), files_with_matches (limits file paths), count (limits count entries). When unspecified, shows all results from ripgrep.")
    multiline: Optional[bool] = Field(False, description="Enable multiline mode where . matches newlines and patterns can span lines (rg -U --multiline-dotall). Default: false.")
    
    def run(self):
        try:
            # Check if ripgrep is available
            try:
                subprocess.run(["rg", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                return "Error: ripgrep (rg) is not installed. Please install ripgrep first."
            
            # Build ripgrep command
            cmd = ["rg"]
            
            # Add case insensitive flag
            if getattr(self, "i", None):
                cmd.append("-i")
            
            # Add multiline flag
            if self.multiline:
                cmd.extend(["-U", "--multiline-dotall"])
            
            # Add file type filter
            if self.type:
                cmd.extend(["--type", self.type])
            
            # Add glob filter
            if self.glob:
                cmd.extend(["--glob", self.glob])
            
            # Handle output mode
            if self.output_mode == "files_with_matches":
                cmd.append("-l")
            elif self.output_mode == "count":
                cmd.append("-c")
            elif self.output_mode == "content":
                # Add line numbers if requested
                if getattr(self, "n", None):
                    cmd.append("-n")
                
                # Add context lines
                if getattr(self, "C", None):
                    cmd.extend(["-C", str(getattr(self, "C"))])
                elif getattr(self, "A", None) or getattr(self, "B", None):
                    if getattr(self, "A", None):
                        cmd.extend(["-A", str(getattr(self, "A"))])
                    if getattr(self, "B", None):
                        cmd.extend(["-B", str(getattr(self, "B"))])
            
            # Add pattern
            cmd.append(self.pattern)
            
            # Add search path
            if self.path:
                cmd.append(self.path)
            else:
                cmd.append(".")
            
            # Execute ripgrep
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=os.getcwd()
                )
                
                output = result.stdout
                
                # Handle empty results
                if not output and result.returncode != 0:
                    if result.stderr:
                        return f"Error: {result.stderr.strip()}"
                    else:
                        return f"No matches found for pattern: {self.pattern}"
                
                # Apply head_limit if specified
                if self.head_limit and output:
                    lines = output.split('\n')
                    if len(lines) > self.head_limit:
                        output = '\n'.join(lines[:self.head_limit])
                        output += f"\n... (output limited to first {self.head_limit} lines)"
                
                return output.strip() if output else f"No matches found for pattern: {self.pattern}"
                
            except subprocess.TimeoutExpired:
                return "Error: Search timed out after 30 seconds"
                
        except Exception as e:
            return f"Error during grep search: {str(e)}"



# Create alias for Agency Swarm tool loading (expects class name = file name)
grep = Grep

if __name__ == "__main__":
    # Test basic search
    tool = Grep(pattern="import", output_mode="files_with_matches")
    print("Files with 'import':")
    print(tool.run())
    
    # Test content search with line numbers
    tool2 = Grep(pattern="class", output_mode="content", n=True, head_limit=5)
    print("\n" + "="*50 + "\n")
    print("Content search for 'class':")
    print(tool2.run())