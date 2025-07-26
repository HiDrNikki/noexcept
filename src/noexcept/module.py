# no.py
from __future__ import annotations
import threading
from typing import Dict, List, Optional, Tuple, Type, Set
no: NoModule
"""
A callable interface for structured exceptions in Python.

Import
------
```python
from noexcept import no
```
Registering Error Codes
-----------------------
Register a normal (raising) error
```python
no.register(404, "Resource not found")
```
Register a soft (non-raising) error
```python
no.register(1001, "Minor warning", soften=True)
```
Basic Usage
-----------

1) Raising an exception (outside any existing exception):
```python
try:
    no(404)

except no.xcpt as noexcept:
    print(str(noexcept))

    # [404]
    # Resource not found
```
2) Attaching to an existing exception (inside an except block):
```python
try:
    risky_operation()

except ValueError as ve:
    # Wrap the ValueError in a new no.xcpt with code 500
    no(500, ve)
```
This will raise a no.xcpt whose message includes both [500] and the original ValueError context

3) Adding extra custom messages:
```python
try:
    no(404, message="User ID 123 not found")

except no.xcpt as noexcept:
    print(str(noexcept))

    # [404]
    # Resource not found
    # User ID 123 not found
```
4) Soft errors (accumulate without immediate raise):
```python
no(1001)      # no exception is raised, because code 1001 was registered with soften=True
```

5) Bundling multiple codes into an ExceptionGroup:
```python
try:
    no([404, 500])
    
except ExceptionGroup as eg:
    for sub in eg.exceptions:
        print(sub)
```
6) Inspecting soft codes:  
  You can inspect `.codes` and `.linked` attributes on a caught `no.xcpt` to see all accumulated codes and wrapped exceptions.
```python
try:
    no(404)

except no.xcpt as noexcept:
    print(noexcept.codes)  # {404: ["Resource not found"]}
    print(noexcept.linked)  # {} (no linked exceptions)
    no(500, "Server error")
```
or even interrogate via if statements:
```python
try:
    no(404)

except no.xcpt as noexcept:
    if 404 in noexcept.codes:
        print("404 detected in codes")
```

See the project README for more examples and the full API reference.
"""

class NoBaseError(Exception):
    """
    Base class for all exceptions raised by the noexcept module.

    Attributes
    ----------
    codes : List[int]
        The numeric error codes attached to this exception (in order of registration or propagation).

    messages : List[str]
        The default and any appended custom messages for each code in `codes`.

    linked : List[Exception]
        Any underlying exceptions that have been linked into this one (e.g. via propagation or direct linking).

    soften : bool
        If True, this code was registered or called in “soft” mode and won't automatically raise when invoked.

    Usage
    -----
    1. Raising directly via `no()` or instantiating yourself:
    ```python
    import no

    no.register(404, "Not Found")

    try:
        no(404)

    except no.xcpt as noexcept:
        print(noexcept.codes)

        # [404]
        # Not Found
    ```
    2. Inspecting codes, messages, and linked exceptions:
    ```python
    try:
        no(403)

    except no.xcpt as noexcept:
        print(noexcept.codes)      # [403]
        print(noexcept.messages)   # ["Forbidden"] (assuming you registered 403 → "Forbidden")
    ```
    3. Chaining an existing exception:
    ```python
    try:
        raise KeyError("missing key")

    except KeyError as ke:
        no(500, ke)  # wraps KeyError under code 500

        Traceback (most recent call last):
                ...
            no.xcpt: [500]
            Server error
            └─ linked KeyError: 'missing key'
    ```
    The original KeyError appears in `noexcept.linked`.
    """

    def __init__(
        self,
        code: int,
        message: Optional[str] = None,
        codes: Optional[Dict[int, List[str]]] = None,
        linked: Optional[
            Dict[Tuple[type, str], Set[Tuple[Optional[str], Optional[int]]]]
        ] = None,
        defaultMessage: Optional[str] = None,
        softCodes: Optional[Dict[int, bool]] = None
    ):

        self.codes: Dict[int, List[str]] = {} if codes is None else codes
        if code not in self.codes:
            self.codes[code] = [defaultMessage or f"Error {code}"]
        if message:
            self.codes[code].append(message)

        self._softCodes: Dict[int, bool] = {} if softCodes is None else softCodes
        self.linked: Dict[Tuple[type, str], Set[Tuple[Optional[str], Optional[int]]]] = (
            {} if linked is None else linked
        )

        super().__init__(self._composeText())

    def _composeText(self) -> str:

        parts = [f"[{','.join(map(str, self.codes.keys()))}]"]
        for code, msgs in self.codes.items():
            parts.extend(msgs)
        return "\n".join(parts)

    def addMessage(self, code: int, message: Optional[str]) -> None:

        if message:
            self.codes.setdefault(code, []).append(message)

    def addCode(self, code: int, defaultMessage: Optional[str] = None) -> None:

        if code not in self.codes:
            self.codes[code] = [defaultMessage or f"Error {code}"]

    def _recordLinkedException(self, exc: BaseException) -> None:

        key = (type(exc), str(exc))
        tb = exc.__traceback__
        if tb:
            while tb.tb_next:
                tb = tb.tb_next
            loc = (tb.tb_frame.f_code.co_filename, tb.tb_lineno)
        else:
            loc = (None, None)
        self.linked.setdefault(key, set()).add(loc)

    def __call__(self, *args, **kwargs) -> None:
        return _handleCall(self, False, *args, **kwargs)

    def __str__(self) -> str:
        parts = [f"[{','.join(map(str, self.codes.keys()))}]"]
        for code, msgs in self.codes.items():
            parts.extend(msgs)

        tb = self.__traceback__
        if tb:
            while tb.tb_next:
                tb = tb.tb_next
            parts.append(f"Raised at {tb.tb_frame.f_code.co_filename}:{tb.tb_lineno}")

        if self.__context__ is not None:
            parts.append(f"context: {type(self.__context__).__name__}: {self.__context__}")
        if self.__cause__ is not None:
            parts.append(f"cause: {type(self.__cause__).__name__}: {self.__cause__}")

        if self.linked:
            parts.append("linked:")
            for (exc_type, msg), locations in self.linked.items():
                loc_text = ", ".join(
                    f"{f}:{ln}" if f else "unknown" for f, ln in sorted(locations)
                )
                parts.append(f"  {exc_type.__name__}: {msg} @ {loc_text}")

        return "\n".join(parts)


class NoModule:
    xcpt: type["NoBaseError"]

    def __init__(self):
        self._registry: Dict[int, Tuple[Type[NoBaseError], str, List[int], bool]] = {}
        self._lock = threading.Lock()

    def register(
        self,
        code: int,
        defaultMessage: str = "",
        linkedCodes: Optional[List[int]] = None,
        *,
        soft: bool = False
    ) -> None:
        """
        Register a new error code with the noexcept module.

        This creates a new subclass of `NoBaseError` named `Error{code}`, makes it
        available as an attribute on the module (e.g. `no.Error404`), and stores its
        default message, any linked codes, and soft-flag in the registry.

        Parameters
        ----------
        code : int
            Numeric identifier for the error. This is the value you pass to `no(code)`
            to raise or reference this exception.

        defaultMessage : str, optional
            Human-readable default message for this code. If omitted or empty,
            a generic `"Error {code}"` message will be used.

        linkedCodes : Optional[List[int]], optional
            Other registered codes whose exceptions will automatically be linked
            whenever this code is raised. Useful for grouping common error causes.

        soft : bool, default False
            If True, calling `no(code)` will not immediately raise an exception
            (soft mode), allowing warnings or deferred checks.

        Examples
        --------
        1) Basic registration:
        ```python
        import no

        no.register(404, "Not Found")

        try:
            no(404)

        except no.xcpt as noexcept:
            print(noexcept)

            [404]
            Not Found
        ```
        2) Soft registration (accumulate without raising):
        ```python
        no.register(1001, "Minor warning", soft=True)

        no(1001)      # no exception is thrown immediately
        ```
        3) Registration with linked codes:
        ```python
        no.register(500, "Server Error", linkedCodes=[404, 403])

        try:
            no(500)

        except no.xcpt as noexcept:
            print(noexcept.codes)

            [500, 404, 403]
        ```
        4) Using the generated exception subclass directly:
        ```python
        raise no.Error500("Custom override message")
        ```
        """
        with self._lock:
            name = f"Error{code}"
            excType = type(name, (NoBaseError,), {})
            setattr(self, name, excType)
            self._registry[code] = (
                excType,
                defaultMessage or f"Error {code}",
                linkedCodes or [],
                soft
            )

    def __call__(self, *args, **kwargs) -> None:
        return _handleCall(self, True, *args, **kwargs)

    def _makeOne(
        self,
        code: int,
        message: Optional[str],
        linked: Optional[List[BaseException]]
    ) -> NoBaseError:
        with self._lock:
            excType, defaultMsg, linkedCodes, softFlag = self._registry.get(
                code, (NoBaseError, f"Error {code}", [], False)
            )
        softCodes = {code: softFlag}
        exc = excType(code, message, defaultMessage=defaultMsg, linked={}, softCodes=softCodes)
        if linked:
            for l in linked:
                exc._recordLinkedException(l)
        for extra in linkedCodes:
            msg = self._registry.get(extra, (None, f"Error {extra}", [], False))[1]
            extraSoft = self._registry.get(extra, (None, "", [], False))[3]
            exc.addCode(extra, msg)
            exc._softCodes[extra] = extraSoft
        return exc

    def propagate(self, exc: NoBaseError, newCode: int) -> None:
        msg = self._registry.get(newCode, (None, f"Error {newCode}", [], False))[1]
        soft = self._registry.get(newCode, (None, "", [], False))[3]
        exc.addCode(newCode, msg)
        exc._softCodes[newCode] = soft

    def language(self, lang: str) -> None:
        """
        Language support is not implemented yet.
        """
        raise NotImplementedError("Language support not implemented yet.")
    
def _handleCall(context, isModule: bool, *args, **kwargs):
    import inspect
    import sys

    message = kwargs.pop("message", None)
    linked = kwargs.pop("linked", None)
    soften = kwargs.pop("soften", False)

    if kwargs:
        raise TypeError(f"Unsupported keyword args: {kwargs}")

    exc_type, exc_value, exc_tb = sys.exc_info()

    # For NoModule, registry is context._registry
    registry = context._registry if isModule else None

    # Handle list of codes
    if len(args) == 1 and isinstance(args[0], list):
        codes = args[0]
        frame = inspect.stack()[1]
        caller = f"{frame.filename}:{frame.lineno}"
        if isModule:
            exceptions = [context._makeOne(c, message, linked) for c in codes]
        else:
            exceptions = [context.__class__(c, message) for c in codes]
        raise ExceptionGroup("Multiple errors", exceptions)

    # no(exc): no-op for module calls
    if len(args) == 1 and isinstance(args[0], BaseException):
        return

    # no(code)
    if len(args) == 1 and isinstance(args[0], int):
        code = args[0]
        soft = (context._registry.get(code, (None, "", [], False))[3]
                if isModule else context._softCodes.get(code, False))

        # MODULE-PROPAGATION: append to existing NoBaseError
        if isModule and isinstance(exc_value, NoBaseError):
            context.propagate(exc_value, code)
            if message:
                exc_value.addMessage(code, message)
            exc_value._softCodes[code] = soft
            if soft or soften:
                return
            raise exc_value.with_traceback(exc_tb)

        # INSTANCE-PROPAGATION
        if not isModule and isinstance(exc_value, NoBaseError):
            defaultMsg = (registry.get(code, (None, f"Error {code}", [], soft))[1]
                          if registry else f"Error {code}")
            exc_value.addCode(code, defaultMsg)
            exc_value.addMessage(code, message)
            exc_value._softCodes[code] = soft
            if soft or soften:
                return
            raise exc_value.with_traceback(exc_tb)

        # fresh new exception
        frame = inspect.stack()[1]
        caller = f"{frame.filename}:{frame.lineno}"
        if isModule:
            exc = context._makeOne(code, message, linked)
        else:
            exc = context.__class__(code, message)
        if soft or soften:
            return
        raise exc

    # no(code, exc)
    if len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], BaseException):
        code, exc_to_link = args
        soft = (context._registry.get(code, (None, "", [], False))[3]
                if isModule else context._softCodes.get(code, False))
        if isModule:
            exc = context._makeOne(code, message, [exc_to_link])
            frame = inspect.stack()[1]
            caller = f"{frame.filename}:{frame.lineno}"
            if soft or soften:
                return
            raise exc.with_traceback(exc_tb)
        else:
            context._recordLinkedException(exc_to_link)
            if soft or soften:
                return
            raise context.with_traceback(exc_tb)

    # no(code, str)
    if len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], str):
        code, msg = args
        soft = (context._registry.get(code, (None, "", [], False))[3]
                if isModule else context._softCodes.get(code, False))

        # MODULE-MESSAGE-APPEND
        if isModule and isinstance(exc_value, NoBaseError):
            context.propagate(exc_value, code)
            exc_value.addMessage(code, msg)
            exc_value._softCodes[code] = soft
            if soft or soften:
                return
            raise exc_value.with_traceback(exc_tb)

        # INSTANCE-MESSAGE-APPEND
        if not isModule and isinstance(exc_value, NoBaseError):
            context.addCode(code)
            context.addMessage(code, msg)
            if soft or soften:
                return
            raise exc_value.with_traceback(exc_tb)

        # fresh new exception
        if isModule:
            frame = inspect.stack()[1]
            caller = f"{frame.filename}:{frame.lineno}"
            exc = context._makeOne(code, msg, linked)
        else:
            context.addCode(code)
            context.addMessage(code, msg)
            exc = context
        if soft or soften:
            return
        raise exc

    raise TypeError(f"Unsupported arguments for no(): {args}")

no = NoModule()
no.xcpt = NoBaseError

__all__ = ["no"]