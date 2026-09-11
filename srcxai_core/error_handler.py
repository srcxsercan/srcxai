"""
Error Handling and Stability Mechanisms
Provides robust error handling, logging, and recovery mechanisms
"""

import logging
import sys
import traceback
import functools
import time
from typing import Callable, Optional, Dict, Any
from datetime import datetime
import json
import os


class ErrorHandler:
    """Centralized error handling for SRCXAI"""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or os.path.join(
            os.path.expanduser('~'), 'srcxai_workspace', 'error.log'
        )
        self._setup_logging()
        self.error_counts: Dict[str, int] = {}
        self.max_retries = 3
        self.retry_delay = 1
    
    def _setup_logging(self):
        """Setup logging configuration"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('SRCXAI')
    
    def handle_error(self, error: Exception, context: Optional[Dict] = None):
        """Handle an error with logging and context"""
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        error_info = {
            'type': error_type,
            'message': str(error),
            'context': context or {},
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc()
        }
        
        self.logger.error(f"Error occurred: {json.dumps(error_info, indent=2)}")
        
        # Check if error is occurring too frequently
        if self.error_counts[error_type] > 10:
            self.logger.critical(f"Error {error_type} occurring too frequently")
    
    def retry_on_failure(self, max_retries: Optional[int] = None, 
                        delay: Optional[float] = None,
                        exceptions: tuple = (Exception,)):
        """Decorator for retrying functions on failure"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                retries = max_retries or self.max_retries
                current_delay = delay or self.retry_delay
                
                for attempt in range(retries):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        if attempt == retries - 1:
                            self.handle_error(e, {'function': func.__name__, 'attempt': attempt + 1})
                            raise
                        
                        self.logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= 2  # Exponential backoff
                
                return None
            return wrapper
        return decorator
    
    def safe_execute(self, func: Callable, *args, **kwargs) -> tuple[bool, Any]:
        """Safely execute a function and return (success, result)"""
        try:
            result = func(*args, **kwargs)
            return True, result
        except Exception as e:
            self.handle_error(e, {'function': func.__name__})
            return False, str(e)
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return self.error_counts.copy()
    
    def reset_error_counts(self):
        """Reset error counts"""
        self.error_counts.clear()


class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker"""
        if self.last_failure_time is None:
            return True
        
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0
        self.state = 'closed'
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
    
    def get_state(self) -> str:
        """Get current circuit breaker state"""
        return self.state


class RateLimiter:
    """Rate limiter for preventing API abuse"""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def allow_call(self) -> bool:
        """Check if a call is allowed"""
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.time_window]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def get_wait_time(self) -> float:
        """Get time to wait before next call is allowed"""
        if len(self.calls) < self.max_calls:
            return 0.0
        
        oldest_call = self.calls[0]
        wait_time = self.time_window - (time.time() - oldest_call)
        return max(0.0, wait_time)


class HealthChecker:
    """Health checking for system components"""
    
    def __init__(self):
        self.components: Dict[str, Callable] = {}
        self.health_status: Dict[str, bool] = {}
    
    def register_component(self, name: str, check_func: Callable):
        """Register a component for health checking"""
        self.components[name] = check_func
    
    def check_component(self, name: str) -> bool:
        """Check health of a specific component"""
        if name not in self.components:
            return False
        
        try:
            is_healthy = self.components[name]()
            self.health_status[name] = is_healthy
            return is_healthy
        except:
            self.health_status[name] = False
            return False
    
    def check_all(self) -> Dict[str, bool]:
        """Check health of all components"""
        for name in self.components:
            self.check_component(name)
        return self.health_status.copy()
    
    def get_healthy_components(self) -> List[str]:
        """Get list of healthy components"""
        return [name for name, status in self.health_status.items() if status]
    
    def get_unhealthy_components(self) -> List[str]:
        """Get list of unhealthy components"""
        return [name for name, status in self.health_status.items() if not status]


class RecoveryManager:
    """Manages recovery procedures for failed components"""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
        self.recovery_procedures: Dict[str, Callable] = {}
    
    def register_recovery(self, component: str, recovery_func: Callable):
        """Register a recovery procedure for a component"""
        self.recovery_procedures[component] = recovery_func
    
    def attempt_recovery(self, component: str) -> bool:
        """Attempt to recover a failed component"""
        if component not in self.recovery_procedures:
            self.error_handler.logger.warning(f"No recovery procedure for {component}")
            return False
        
        try:
            self.error_handler.logger.info(f"Attempting recovery for {component}")
            success = self.recovery_procedures[component]()
            
            if success:
                self.error_handler.logger.info(f"Recovery successful for {component}")
            else:
                self.error_handler.logger.error(f"Recovery failed for {component}")
            
            return success
        except Exception as e:
            self.error_handler.handle_error(e, {'component': component, 'action': 'recovery'})
            return False


def setup_global_error_handling(log_file: Optional[str] = None) -> ErrorHandler:
    """Setup global error handling for the application"""
    error_handler = ErrorHandler(log_file)
    
    # Setup global exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_handler.handle_error(exc_value, {
            'type': exc_type.__name__,
            'uncaught': True
        })
    
    sys.excepthook = handle_exception
    
    return error_handler
