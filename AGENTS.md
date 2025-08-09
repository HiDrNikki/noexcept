# noexcept - AI Agent Reference

Lightweight numbered exception handler for Python. Thread-safe and multi-process safe via rememory backend.

## Installation
```bash
pip install noexcept
```

## Core API

```python
from noexcept import no

# Register error codes
no.likey(404, "Not Found")                # Standard error
no.likey(500, "Server Error", soft=True)  # Soft error (accumulates)

# Raise exceptions  
no(404)                    # Raise code 404
no(404, "Custom message")  # With custom message
no([404, 500])            # Multiple codes (ExceptionGroup)
no(404, exception_obj)     # Link existing exception

# Soft error handling
no(500)           # Accumulates if registered as soft
no.bueno          # Bool: True if soft errors accumulated
no.nos            # Dict: {code: [messages]}
no.complaints     # List: All error messages
no.dice()         # Clear all pending errors

# Exception handling
try:
    no(404)
except no.way as e:
    print(e.nos)  # {404: ["Not Found"]}

# Safe execution
with no.go(500):
    risky_operation()  # Any exception becomes code 500

result = no.go(404, func, *args, soften=True)

# Builder pattern
exc = (no.build()
       .withCode(404, "Page missing")
       .withCode(500, "Server error") 
       .asSoft(404)
       .build())
```

## Key Features

- **Thread-safe**: All operations safe across threads
- **Multi-process safe**: State persists via rememory
- **Soft errors**: Accumulate without raising
- **Exception linking**: Chain exceptions with context
- **ExceptionGroup support**: Multiple codes in single exception
- **Builder pattern**: Fluent exception construction

## Exception Class

`no.way` - Base exception class with:
- `.nos` - Dict of codes and messages
- `.complaints` - Flattened message list  
- `.linked` - Dict of linked exceptions

## Use Cases

1. **API error codes**: Clean numbered responses
2. **Batch processing**: Accumulate soft errors  
3. **Multi-threaded apps**: Thread-safe error handling
4. **Process chains**: Multi-process error persistence
5. **Error aggregation**: Collect multiple failure points

## Performance

Optimized for:
- Minimal memory overhead
- Fast exception creation
- Efficient string operations
- Thread-local caching
