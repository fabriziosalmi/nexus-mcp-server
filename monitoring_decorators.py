# -*- coding: utf-8 -*-
# monitoring_decorators.py - Decorators for adding monitoring to functions
import time
import functools
from monitoring import get_monitoring


def monitor_tool_execution(func):
    """
    Decorator that adds Prometheus monitoring to tool execution functions.
    Tracks execution time and status (success/error) for each tool call.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract tool_name from request argument
        request = None
        for arg in args:
            if hasattr(arg, 'tool_name'):
                request = arg
                break
        
        if not request:
            # Fallback to original function if we can't find the request
            return await func(*args, **kwargs)
        
        tool_name = request.tool_name
        start_time = time.time()
        monitoring = get_monitoring()
        
        try:
            # Execute the original function
            result = await func(*args, **kwargs)
            
            # Record successful execution
            duration = time.time() - start_time
            monitoring.record_tool_call(tool_name, "success", duration)
            
            return result
            
        except Exception as e:
            # Record failed execution
            duration = time.time() - start_time
            monitoring.record_tool_call(tool_name, "error", duration)
            raise e
    
    return wrapper


def monitor_sync_tool_execution(func):
    """
    Decorator for synchronous tool execution functions.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract tool_name from arguments (assumes first arg has tool_name)
        tool_name = "unknown"
        for arg in args:
            if hasattr(arg, 'tool_name'):
                tool_name = arg.tool_name
                break
        
        start_time = time.time()
        monitoring = get_monitoring()
        
        try:
            # Execute the original function
            result = func(*args, **kwargs)
            
            # Record successful execution
            duration = time.time() - start_time
            monitoring.record_tool_call(tool_name, "success", duration)
            
            return result
            
        except Exception as e:
            # Record failed execution
            duration = time.time() - start_time
            monitoring.record_tool_call(tool_name, "error", duration)
            raise e
    
    return wrapper