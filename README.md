# No Exceptions

A callable interface for structured exceptions in Python, allowing dynamic registration of error codes, soft (non-raising) codes, exception propagation with context, and grouping multiple errors.

### Features

* **Dynamic Error Codes:** Register custom error codes with default complaints at runtime.
* **Soft Errors:** Define codes that don’t immediately raise exceptions, useful for warning accumulation.
* **Error Propagation:** Wrap existing exceptions under new error codes while preserving context.
* **Exception Linking:** Attach underlying exceptions to your custom errors for full traceability.
* **ExceptionGroup Support:** Bundle multiple error codes into a single ExceptionGroup.
* **Rich String Output:** Automatically include codes, complaints, linked exceptions, and stack traces when converting to string.

## Installation

Requires Python 3.11 or newer.

### With PIP

```bash
pip install noexcept
```

### With GitHub

```bash
pip install git+https://github.com/HiDrNikki/noexcept.git

pip install git+https://github.com/HiDrNikki/noexcept.git@v1.2.2

pip install -e git+https://github.com/HiDrNikki/noexcept.git@main#egg=noexcept
```

## Quick Start

Import the callable exception handler and register your error codes:

```python
from noexcept import no
```

### Register codes at startup

```python
no.likey(404, "Not Found")            # Standard error
no.likey(500, "Server Error")         # Standard error
no.likey(123, "Soft Error", soft=True)  # Soft (non-raising)
```

### Raising an Exception

```python
from noexcept import no

try:
    no(404)
except no.way as noexcept:
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
        no(500, ve)  # Raises a no.way with 500 as the linked ValueError
    except no.way as noexcept:
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
### no.go

`no.go` provides a context manager for cleanly handling exceptions:

```python
with no.go(404):
    raise ValueError("Original issue")  # Automatically wrapped under code 404
```
It can also be used in line to run a callable, and raise an error code if it fails.
```python
result = no.go(404, myFunction, *args, **kwargs, soften = True)
```
In both cases the raw error that is thrown is linked to whatever code is passed.
### no.bueno

`no.bueno` indicates if any soft errors have yet been registered:

```python
no(123)
if not no.bueno:
    print("Issues detected")
```

### no.nos

`no.nos` contains details of all registered error codes:

```python
print(no.nos)
# {404: 'Not Found', 500: 'Server Error', 123: 'Soft Error'}
```

### no.complaints

`no.complaints` accumulates soft error messages:

```python
no(123)
no(123, "Extra warning detail")

print(no.complaints)
# ['Soft Error', 'Soft Error: Extra warning detail']
```

## API Reference
### Import the handler
```python
from noexcept import no
```
### Register error codes
```python
no.likey(code: int, complaint: str, soften: bool = False)
```
### Raise exceptions
```python
no(code: int | list[int] | Exception, complaint: str = None, soften: bool = False)
```
### Base exception type
```python
no.way
```
### Inline error safe code execution, or context manager
```python
no.go
```
### A boolean indicating whether any soft errors have been triggered yet
```python
no.bueno
```
### A dictionary containing all the currently triggered codes
```python
no.nos
```
### A flat list of all of the error messages
```python
no.complaints
```
### Clears the pending exception, along with all codes and messages
```python
no.dice()
```

## Contributing

Contributions are welcome! Please open issues and pull requests on GitHub.

## License

This project is licensed under the MIT License. See LICENSE for details.

Authored by Nichola Walch [littler.compression@gmail.com](mailto:littler.compression@gmail.com)
