# monkey_patch.py
import sys
import typing
from typing import ForwardRef, Any

# Only apply the patch for Python 3.13+
if sys.version_info >= (3, 13):
    # Store the original _evaluate method
    original_evaluate = ForwardRef._evaluate
    
    # Create a patched version that handles the new recursive_guard parameter
    def patched_evaluate(self, globalns, localns, recursive_guard=None):
        if recursive_guard is None:
            recursive_guard = set()
        # Call the original with the keyword argument
        return original_evaluate(globalns, localns, recursive_guard=recursive_guard)
    
    # Apply the patched method
    ForwardRef._evaluate = patched_evaluate
    
    # If you're using pydantic v1, also patch its evaluate_forwardref function
    try:
        from pydantic.v1.typing import evaluate_forwardref
        
        def patched_evaluate_forwardref(type_, globalns, localns):
            # Use the correct signature for Python 3.13
            return type_._evaluate(globalns, localns, recursive_guard=set())
        
        # Replace the original function with our patched version
        import pydantic.v1.typing
        pydantic.v1.typing.evaluate_forwardref = patched_evaluate_forwardref
        
        print("Successfully applied monkey patch for ForwardRef._evaluate in Python 3.13")
    except ImportError:
        # pydantic v1 might not be available
        pass