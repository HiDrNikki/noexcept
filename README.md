# No Exceptions




A callable interface for structured exceptions in Python, allowing dynamic registration of error codes, soft (non-raising) codes, exception propagation with context, and grouping multiple errors.

### Features

Dynamic Error Codes: Register custom error codes with default messages at runtime.

Soft Errors: Define codes that don’t immediately raise exceptions, useful for warning accumulation.

Error Propagation: Wrap existing exceptions under new error codes while preserving context.

Exception Linking: Attach underlying exceptions to your custom errors for full traceability.

ExceptionGroup Support: Bundle multiple error codes into a single ExceptionGroup.

Rich String Output: Automatically include codes, messages, linked exceptions, and stack traces when converting to string.

## Installation

Requires Python 3.11 or newer.

### From PyPI
```python
pip install noexcept
```
## Quick Start

Import the callable exception handler and register your error codes:

```python
from noexcept import no
```
### Register codes at startup
```python
no.register(404, "Not Found")            # Standard error

no.register(500, "Server Error")         # Standard error

no.register(123, "Soft Error", soft=True)  # Soft (non-raising)
```
### Raising an Exception
```python
from noexcept import no

try:
    no(404)

except no.xcpt as noexcept:
    print(str(noexcept))

    # [404]
    # Not Found
```
### Soft Errors

Soft codes don’t immediately raise:
```python
no(123)  # No exception is thrown because code 123 is registered as soft
```
### Propagating Errors

Wrap an existing exception under a new code:
```python
try:
    raise ValueError("underlying issue")

except ValueError as ve:
    try:
        no(500, ve)  # Raises a no.xcpt with 500 as the linked ValueError

    except no.xcpt as noexcept:
        print(noexcept)
```
### Linking Underlying Exceptions

Add an existing exception to a new code without raising immediately:
```python
try:
    raise KeyError("missing key")

except KeyError as ke:
    no(404, ke, soften=True)
```
### Grouping Multiple Errors

Bundle multiple codes in one go:
```python
try:
    no([404, 500])
    
except ExceptionGroup as eg:
    for subexc in eg.exceptions:
        print(subexc)
```
### API Reference
```python
no.register(code: int, message: str, soften: bool = False)
```
### Register a new error code.
```python
code: Numeric identifier.

message: Default message for the code.

soften: If True, calling this code won’t raise immediately.

no(code: int | list[int] | Exception, message: str = None, soften: bool = False)
```
### Invoke or raise an error:
```python
Single int: Raise or return a no.xcpt for that code.

list[int]: Raises an ExceptionGroup of all specified codes.

Existing Exception: Links this exception under your codes.

message: Append an extra message to the error.

soften: Suppresses immediate raising for soft usage.

no.xcpt
```
Base exception type for all registered errors. Inherits rich context and linking support.

## Contributing

Contributions are welcome! Please open issues and pull requests on GitHub.

## License

This project is licensed under the MIT License. See LICENSE for details.

Authored by Nichola Walch littler.compression@gmail.com