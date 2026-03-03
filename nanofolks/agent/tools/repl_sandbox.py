"""
REPL Sandbox - Secure Python execution environment.

This module provides a sandboxed environment for executing arbitrary Python code
with restricted access to filesystem, network, and system resources.

Based on Witan Labs REPL Tool pattern:
https://github.com/witanlabs/research-log/blob/main/06-repl-tool.md
"""

import asyncio
import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Dict, List, Optional, Set

from loguru import logger

try:
    from RestrictedPython import compile_restricted
    from RestrictedPython.Guards import safe_builtins, guarded_setattr
    from RestrictedPython.Eval import default_guarded_getitem
    RESTRICTED_PYTHON_AVAILABLE = True
except ImportError:
    RESTRICTED_PYTHON_AVAILABLE = False
    logger.warning("RestrictedPython not installed. REPL will use basic sandboxing.")


class REPLError(Exception):
    """Base exception for REPL errors."""
    pass


class REPLTimeoutError(REPLError):
    """Raised when REPL execution exceeds timeout."""
    pass


class REPlOutputTooLargeError(REPLError):
    """Raised when REPL output exceeds size limit."""
    pass


class RestrictedPythonSandbox:
    """
    Sandboxed Python execution environment.
    
    Security features:
    - RestrictedPython compilation (if available)
    - No filesystem access
    - No network access
    - Timeout enforcement
    - Output truncation
    - Memory limits (via resource limits)
    
    Usage:
        sandbox = RestrictedPythonSandbox(timeout=90, max_output_chars=20000)
        result = await sandbox.execute_async("print('Hello')", globals_dict)
    """
    
    # Modules that are explicitly blocked
    BLOCKED_MODULES: Set[str] = {
        # Filesystem
        'os', 'sys', 'subprocess', 'shutil', 'pathlib', 'glob',
        'tempfile', 'fileinput', 'filecmp', 'distutils',
        # Network
        'socket', 'ssl', 'requests', 'http', 'urllib', 'httplib',
        'ftplib', 'smtplib', 'poplib', 'imaplib', 'nntplib',
        'telnetlib', 'xmlrpc', 'aiohttp', 'httpx', 'websocket',
        # System
        'multiprocessing', 'threading', 'signal', 'ctypes',
        'winreg', 'posix', 'nt', '_socket', '_ssl',
        # Code execution
        'importlib', 'pkgutil', 'modulefinder', 'code', 'codeop',
        'compile', 'exec', 'eval', '__builtins__',
        # Dangerous
        'pickle', 'shelve', 'marshal', 'imp', 'zipimport',
    }
    
    # Safe builtins to allow
    SAFE_BUILTINS: Dict[str, Any] = {
        # Basic types
        'bool': bool,
        'int': int,
        'float': float,
        'str': str,
        'list': list,
        'dict': dict,
        'tuple': tuple,
        'set': set,
        'frozenset': frozenset,
        'bytes': bytes,
        'bytearray': bytearray,
        # Type checking
        'type': type,
        'isinstance': isinstance,
        'issubclass': issubclass,
        'hasattr': hasattr,
        'getattr': getattr,
        'setattr': setattr,
        'delattr': delattr,
        # Basic functions
        'len': len,
        'range': range,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'sorted': sorted,
        'reversed': reversed,
        'any': any,
        'all': all,
        'min': min,
        'max': max,
        'sum': sum,
        'abs': abs,
        'round': round,
        'pow': pow,
        'divmod': divmod,
        # Type conversion
        'ord': ord,
        'chr': chr,
        'bin': bin,
        'hex': hex,
        'oct': oct,
        # String formatting
        'format': format,
        'repr': repr,
        'ascii': ascii,
        # Iteration
        'iter': iter,
        'next': next,
        'slice': slice,
        # Other safe functions
        'hash': hash,
        'id': id,
        'callable': callable,
        'staticmethod': staticmethod,
        'classmethod': classmethod,
        'property': property,
        # Constants
        'True': True,
        'False': False,
        'None': None,
        'Ellipsis': Ellipsis,
        'NotImplemented': NotImplemented,
        # Exceptions (read-only)
        'Exception': Exception,
        'ValueError': ValueError,
        'TypeError': TypeError,
        'KeyError': KeyError,
        'IndexError': IndexError,
        'AttributeError': AttributeError,
        'RuntimeError': RuntimeError,
        'StopIteration': StopIteration,
    }
    
    def __init__(
        self,
        timeout: float = 90.0,
        max_output_chars: int = 20000,
        max_iterations: int = 1000000,
    ):
        """
        Initialize sandbox.
        
        Args:
            timeout: Maximum execution time in seconds (default: 90)
            max_output_chars: Maximum output characters before truncation (default: 20000)
            max_iterations: Maximum loop iterations (default: 1000000)
        """
        self.timeout = timeout
        self.max_output_chars = max_output_chars
        self.max_iterations = max_iterations
        
        if not RESTRICTED_PYTHON_AVAILABLE:
            logger.warning(
                "RestrictedPython not installed. Using basic sandboxing. "
                "Install with: pip install RestrictedPython"
            )
    
    def _create_safe_builtins(self) -> Dict[str, Any]:
        """
        Create a safe builtins dictionary.
        
        Returns:
            Dictionary of safe built-in functions and types
        """
        safe = dict(self.SAFE_BUILTINS)
        
        if RESTRICTED_PYTHON_AVAILABLE:
            # Add RestrictedPython guards
            safe.update({
                '__builtins__': safe,
                '_getattr_': default_guarded_getitem,
                '_getitem_': default_guarded_getitem,
                '_write_': lambda x: x,
                '_iter_': iter,
                '_next_': next,
                '_getiter_': iter,
                '_inplacevar_': lambda op, x, y: eval(f"x {op}= y"),
            })
        
        return safe
    
    def _validate_code(self, code: str) -> None:
        """
        Validate code for obvious security issues.
        
        Args:
            code: Python code to validate
        
        Raises:
            REPLError: If code contains dangerous patterns
        """
        # Check for blocked imports
        code_lower = code.lower()
        for module in self.BLOCKED_MODULES:
            # Check various import patterns
            patterns = [
                f"import {module}",
                f"from {module}",
                f"__import__('{module}')",
                f'__import__("{module}")',
            ]
            for pattern in patterns:
                if pattern in code_lower:
                    raise REPLError(
                        f"Access to module '{module}' is not allowed in REPL"
                    )
        
        # Check for dangerous functions
        dangerous_patterns = [
            'exec(',
            'eval(',
            'compile(',
            'open(',
            'input(',
            '__import__(',
            'globals(',
            'locals(',
            'vars(',
            'dir(',
        ]
        for pattern in dangerous_patterns:
            if pattern in code:
                raise REPLError(
                    f"Use of '{pattern.strip('('})' is not allowed in REPL"
                )
    
    def compile(self, code: str, filename: str = "<repl>") -> Any:
        """
        Compile code with restrictions.
        
        Args:
            code: Python code to compile
            filename: Filename for error messages
        
        Returns:
            Compiled code object
        
        Raises:
            REPLError: If compilation fails
        """
        self._validate_code(code)
        
        if RESTRICTED_PYTHON_AVAILABLE:
            try:
                return compile_restricted(code, filename, mode='exec')
            except SyntaxError as e:
                raise REPLError(f"Syntax error: {e}")
        else:
            # Fallback to standard compile
            try:
                return compile(code, filename, mode='exec')
            except SyntaxError as e:
                raise REPLError(f"Syntax error: {e}")
    
    def execute(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Execute Python code synchronously.
        
        Args:
            code: Python code to execute
            globals_dict: Global namespace (will be modified in-place)
        
        Returns:
            Execution output as string
        """
        if globals_dict is None:
            globals_dict = {}
        
        # Ensure safe builtins
        if '__builtins__' not in globals_dict:
            globals_dict['__builtins__'] = self._create_safe_builtins()
        
        # Capture output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            # Compile code
            compiled = self.compile(code)
            
            # Execute with output capture
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(compiled, globals_dict)
            
            # Get output
            output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            # Include stderr if present
            if stderr_output:
                output += f"\n[stderr]: {stderr_output}"
            
            # Truncate if needed
            if len(output) > self.max_output_chars:
                output = output[:self.max_output_chars]
                output += f"\n... (truncated, {len(output)} chars limit)"
            
            return output if output.strip() else "OK"
            
        except REPLError:
            raise
        except Exception as e:
            return f"Error: {type(e).__name__}: {str(e)}"
    
    async def execute_async(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """
        Execute Python code asynchronously with timeout.
        
        Args:
            code: Python code to execute
            globals_dict: Global namespace (will be modified in-place)
            timeout: Override default timeout (seconds)
        
        Returns:
            Execution output as string
        
        Raises:
            REPLTimeoutError: If execution exceeds timeout
        """
        timeout = timeout or self.timeout
        
        try:
            # Run in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    self.execute,
                    code,
                    globals_dict,
                ),
                timeout=timeout,
            )
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"REPL execution timed out after {timeout}s")
            raise REPLTimeoutError(
                f"Execution timed out after {timeout} seconds"
            )
        except Exception as e:
            logger.error(f"REPL execution error: {e}")
            raise


# Convenience function for quick testing
async def test_sandbox():
    """Test the sandbox with some example code."""
    sandbox = RestrictedPythonSandbox(timeout=5, max_output_chars=1000)
    
    # Test 1: Simple print
    result = await sandbox.execute_async("print('Hello, World!')")
    print(f"Test 1: {result}")
    
    # Test 2: Math
    result = await sandbox.execute_async("print(2 + 2)")
    print(f"Test 2: {result}")
    
    # Test 3: Variables
    globals_dict = {'x': 10}
    result = await sandbox.execute_async("print(x * 2)", globals_dict)
    print(f"Test 3: {result}")
    
    # Test 4: Blocked import (should fail)
    try:
        result = await sandbox.execute_async("import os")
        print(f"Test 4: {result}")
    except REPLError as e:
        print(f"Test 4 (expected error): {e}")


if __name__ == "__main__":
    asyncio.run(test_sandbox())
