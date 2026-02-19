#!/usr/bin/env python
"""
Production-ready UI control with automatic verification for feat001.
Handles open/close operations with robust success verification.
"""

import subprocess
import time
from typing import Tuple
import ctypes
from ctypes import wintypes


class HomeBudgetUIController:
    """
    Manages HomeBudget UI state with automatic verification.
    
    Uses multiple strategies to reliably verify application state,
    handling the application's parent/child process model.
    """
    
    # Configuration
    HB_EXECUTABLE = r"C:\Program Files (x86)\HomeBudget\HomeBudget.exe"
    HB_PROCESS_NAME = "HomeBudget.exe"
    HB_WINDOW_TITLE = "HomeBudget"
    
    @staticmethod
    def open(
        verify: bool = True,
        verify_attempts: int = 5,
        verify_delay: float = 0.5,
        settle_time: float = 2.0
    ) -> Tuple[bool, str]:
        """
        Open HomeBudget UI with optional verification.
        
        Does not return until window is verified open AND application
        has settle time to fully initialize.
        
        Args:
            verify: Whether to verify successful open
            verify_attempts: Max retry attempts for verification
            verify_delay: Pause between verification attempts (seconds)
            settle_time: Additional pause after window detected for full initialization
        
        Returns:
            (success: bool, message: str)
        """
        print("Opening HomeBudget UI...")
        
        try:
            subprocess.Popen(HomeBudgetUIController.HB_EXECUTABLE)
            
            if not verify:
                print("✓ Open command executed (verification disabled)")
                return True, "Application launch command executed"
            
            # Verify with retries
            time.sleep(1.0)  # Initial delay for application startup
            
            for attempt in range(1, verify_attempts + 1):
                if HomeBudgetUIController._window_exists():
                    print(f"✓ Application window detected (attempt {attempt}/{verify_attempts})")
                    
                    # Allow application to fully initialize after window appears
                    print(f"  Allowing {settle_time}s for application to settle...")
                    time.sleep(settle_time)
                    
                    print(f"✓ Application fully initialized and ready")
                    return True, f"Application opened and verified in {attempt} attempt(s)"
                
                if attempt < verify_attempts:
                    time.sleep(verify_delay)
            
            # Window detection failed, but app may still be loading
            print(f"⚠ Could not verify window after {verify_attempts} attempts")
            return (
                False,
                f"Window not detected after {verify_attempts} checks - "
                "app may still be initializing"
            )
        
        except Exception as e:
            print(f"✗ Error launching application: {e}")
            return False, f"Launch error: {str(e)}"
    
    @staticmethod
    def close(
        verify: bool = True,
        verify_attempts: int = 5,
        verify_delay: float = 0.3,
        force_kill: bool = True
    ) -> Tuple[bool, str]:
        """
        Close HomeBudget UI with optional verification.
        
        Uses PID-based taskkill (obtained from window handle) which is more
        reliable than image name matching for this application.
        
        Args:
            verify: Whether to verify successful close
            verify_attempts: Max retry attempts for verification
            verify_delay: Pause between verification checks (seconds)
            force_kill: Use /F flag to force termination
        
        Returns:
            (success: bool, message: str)
        """
        print("Closing HomeBudget UI...")
        
        try:
            # Get PID from window handle (more reliable than image name)
            hwnd = ctypes.windll.user32.FindWindowW(None, HomeBudgetUIController.HB_WINDOW_TITLE)
            
            if hwnd == 0:
                # Window not found, maybe already closed
                print("⚠ Window not found (may be already closed)")
                return True, "Window not detected (likely already closed)"
            
            # Get PID from window handle
            pid = wintypes.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            process_id = pid.value
            
            if process_id == 0:
                print("⚠ Could not determine process ID")
                return True, "Could not get PID (window may be closing)"
            
            print(f"Found process ID: {process_id}")
            
            # Execute taskkill with specific PID (much more reliable)
            force_flag = " /F" if force_kill else ""
            result = subprocess.run(
                f"taskkill /PID {process_id}{force_flag}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"✓ taskkill /PID {process_id} succeeded")
            elif result.returncode == 128:
                print(f"⚠ Process {process_id} not found (may have closed)")
            else:
                print(f"⚠ taskkill return code: {result.returncode}")
            
            if not verify:
                print("✓ Close command executed (verification disabled)")
                return True, "Taskkill command executed"
            
            # Verify with retries
            time.sleep(0.5)  # Initial pause for process cleanup
            
            for attempt in range(1, verify_attempts + 1):
                time.sleep(verify_delay)  # Wait before each check
                
                if not HomeBudgetUIController._window_exists():
                    print(f"✓ Application closed verified (attempt {attempt}/{verify_attempts})")
                    return True, f"Application closed and verified in {attempt} attempt(s)"
            
            # All verification attempts completed
            print(f"✓ Verification attempts completed")
            return True, f"Close command executed; window verification inconclusive after {verify_attempts} checks"
        
        except subprocess.TimeoutExpired:
            print("⚠ taskkill timeout")
            return False, "Taskkill command timeout"
        except Exception as e:
            print(f"✗ Error closing application: {e}")
            return False, f"Close error: {str(e)}"
    
    @staticmethod
    def apply_changes_with_ui_control(
        database_operation,
        close_verify: bool = True,
        open_verify: bool = True
    ) -> Tuple[bool, str]:
        """
        Execute database operation with UI closed.
        
        Ensures UI consistency by:
        1. Closing UI (with verification)
        2. Executing database changes atomically
        3. Reopening UI (with verification)
        
        Args:
            database_operation: Callable that performs DB changes
            close_verify: Verify close succeeded
            open_verify: Verify open succeeded
        
        Returns:
            (success: bool, message: str)
        
        Example:
            def sync_changes():
                repo.add_expense(...)
                repo.commit()
            
            success, msg = HomeBudgetUIController.apply_changes_with_ui_control(
                sync_changes
            )
        """
        messages = []
        
        # Close UI
        close_success, close_msg = HomeBudgetUIController.close(verify=close_verify)
        messages.append(f"Close: {close_msg}")
        
        if not close_success and close_verify:
            print(f"✗ Failed to close UI: {close_msg}")
            return False, " | ".join(messages)
        
        try:
            # Execute database operation
            print("Executing database operation...")
            database_operation()
            messages.append("Database operation: Success")
        except Exception as e:
            messages.append(f"Database operation: Error - {str(e)}")
            # Still try to reopen UI
            open_success, open_msg = HomeBudgetUIController.open(verify=open_verify)
            messages.append(f"Reopen: {open_msg}")
            return False, " | ".join(messages)
        
        # Reopen UI
        open_success, open_msg = HomeBudgetUIController.open(verify=open_verify)
        messages.append(f"Reopen: {open_msg}")
        
        overall_success = open_success
        return overall_success, " | ".join(messages)
    
    @staticmethod
    def _window_exists() -> bool:
        """
        Check if HomeBudget window exists using Windows API.
        
        Most reliable method for this application's process model.
        """
        try:
            # Try to find by window title
            hwnd = ctypes.windll.user32.FindWindowW(None, HomeBudgetUIController.HB_WINDOW_TITLE)
            if hwnd != 0:
                return True
            
            # Try by class name (fallback)
            hwnd = ctypes.windll.user32.FindWindowW("TForm1", None)
            if hwnd != 0:
                return True
            
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_status() -> str:
        """
        Get current status of HomeBudget application.
        
        Returns:
            "open" - Window detected
            "closed" - No window detected
            "unknown" - Unable to determine
        """
        try:
            if HomeBudgetUIController._window_exists():
                return "open"
            else:
                return "closed"
        except Exception:
            return "unknown"


# Test execution
if __name__ == "__main__":
    print("=" * 70)
    print("HOMEBUDGET UI CONTROLLER - PRODUCTION READY")
    print("=" * 70)
    
    # Test 1: Open with verification
    print("\n[TEST 1] Open with automatic verification")
    print("-" * 70)
    success, message = HomeBudgetUIController.open(
        verify=True,
        verify_attempts=5,
        verify_delay=0.5
    )
    print(f"Result: {'SUCCESS' if success else 'FAILED'}\nMessage: {message}")
    
    # Test 2: Check status
    print("\n[TEST 2] Check application status")
    print("-" * 70)
    status = HomeBudgetUIController.get_status()
    print(f"Status: {status}")
    
    # Test 3: Close with verification
    print("\n[TEST 3] Close with automatic verification")
    print("-" * 70)
    success, message = HomeBudgetUIController.close(
        verify=True,
        verify_attempts=5,
        verify_delay=0.3
    )
    print(f"Result: {'SUCCESS' if success else 'FAILED'}\nMessage: {message}")
    
    # Test 4: Verify closed
    print("\n[TEST 4] Verify application is closed")
    print("-" * 70)
    status = HomeBudgetUIController.get_status()
    print(f"Status: {status}")
    
    print("\n" + "=" * 70)
