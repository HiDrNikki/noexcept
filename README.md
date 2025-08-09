# No Exceptions 🚫💥

*A light-hearted, lightweight numbered exception handler for Python*

Tired of boring old try-catch blocks? Want your errors to have personality? Meet **noexcept** - the exception handler that thinks error codes are cooler than plain old stack traces! 

This delightfully punny library lets you register numbered error codes and handle them with style. No more cryptic exceptions - just clean, numbered codes that you can `likey`, accumulate when things go `bueno`, and clear when you say "no `dice`"!

## ✨ What Makes It Special

* **📝 Dynamic Error Codes:** Register custom error codes with witty complaints at runtime
* **🤫 Soft Errors:** Define codes that whisper instead of shout - perfect for warning accumulation  
* **🔗 Error Linking:** Chain exceptions together like a friendship bracelet of failures
* **📦 Exception Groups:** Bundle multiple codes into one neat package (because misery loves company)
* **🧵 Thread-Safe:** Works beautifully across multiple threads without breaking a sweat
* **🚀 Multi-Process Safe:** Thanks to the amazing `rememory` backend, your error codes persist across processes
* **🎯 Lightweight:** Minimal overhead, maximum personality
* **🔧 Builder Pattern:** Fluently construct complex exceptions with `no.build()`

## 📦 Installation

Requires Python 3.8 or newer (because we're not *completely* reckless).

### With PIP

```bash
pip install noexcept
```

### With GitHub

```bash
pip install git+https://github.com/HiDrNikki/noexcept.git

pip install git+https://github.com/HiDrNikki/noexcept.git@v1.5.4

pip install -e git+https://github.com/HiDrNikki/noexcept.git@main#egg=noexcept
```

## 🚀 Quick Start

Time to make your errors more interesting than your code comments!

```python
from noexcept import no

# Register some codes that you actually likey 
no.likey(404, "Not Found")                    # Classic 
no.likey(500, "Server went bye-bye")          # Dramatic
no.likey(418, "I'm a teapot", soft=True)      # RFC compliant and soft
```

### 💥 When Things Go Wrong (But In Style)

```python
try:
    no(404)  # Uh oh, something's missing
except no.way as err:
    print(err)
    # [404]
    # Not Found
```

### 🤫 Soft Errors (The Polite Ones)

Sometimes you want to complain quietly:

```python
no(418)  # This just accumulates, no drama
if no.bueno:  # Check if anything went sideways
    print(f"Issues: {no.complaints}")
```

### 🔗 Exception Linking (Chain Gang Style)

When one error leads to another:

```python
try:
    raise ValueError("Something's fishy")
except ValueError as fishy:
    no(500, fishy)  # Links the ValueError to code 500
```

### 📦 Multiple Errors (Bulk Discount Available)

Why have one error when you can have several?

```python
no([404, 500, 418])  # Triple threat!
# This creates an ExceptionGroup with all three
```

### 🏗️ Builder Pattern (For The Architects)

Sometimes you need to craft the perfect exception:

```python
error = (no.build()
         .withCode(404, "Page missing") 
         .withCode(500, "Server sad")
         .asSoft(404)  # Make 404 soft
         .build())
```
### 🏃‍♂️ no.go (The Safety Net)

Try things safely, with automatic error wrapping:

```python
with no.go(500):
    dangerous_operation()  # Any exception becomes code 500

# Or run a function with built-in error handling
result = no.go(404, risky_function, arg1, arg2, soften=True)
```

## 📚 The Pun-derful API

### 🎯 The Main Players

- **`no.likey(code, complaint, soft=False)`** - Register error codes you actually like
- **`no(code)`** - Raise that code (or go soft if it's registered that way)
- **`no.way`** - The exception class (because there's no way around it)
- **`no.go(code, func=None)`** - Safe execution context or function wrapper  
- **`no.bueno`** - Boolean indicating if soft errors accumulated
- **`no.nos`** - Dictionary of all accumulated error codes and messages
- **`no.complaints`** - List of all error messages (the complaint department)
- **`no.dice()`** - Clear all pending errors (roll the dice again)
- **`no.build()`** - Create a fluent exception builder

## 🚀 Performance & Safety

- **🧵 Thread-Safe**: Handle errors across multiple threads without fear
- **🔄 Multi-Process Safe**: Thanks to `rememory`, your error codes persist across process boundaries  
- **⚡ Lightweight**: Minimal overhead with maximum personality
- **🔧 Optimized**: Built-in caching, efficient string handling, and smart memory management

## 🤝 Why Choose noexcept?

Because life's too short for boring error handling! Whether you're building a web app, API, or just want to add some personality to your error management, noexcept makes exception handling fun again.

Perfect for teams who appreciate:
- Clean, numbered error codes instead of cryptic stack traces
- Soft error accumulation for batch processing  
- Multi-threaded and multi-process applications
- A touch of humor in their development tools

## Contributing

Contributions are welcome! Please open issues and pull requests on GitHub.

## License

This project is licensed under the MIT License. See LICENSE for details.

Authored by Nichola Walch [littler.compression@gmail.com](mailto:littler.compression@gmail.com)
