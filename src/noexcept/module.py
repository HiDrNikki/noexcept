# no.py
from __future__ import annotations
import threading
from typing import Dict, List, Optional, Tuple, Type, Set, overload, Callable, TypeVar, Any, cast
import sys
from contextlib import contextmanager
from .exception import NoBaseException, NoBuilder
from rememory import RMDict, RMBlock, BlockSize

# Constants
DEFAULT_BLOCK_SIZE = 4096

T = TypeVar("T")
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
no.likey(404, "Resource not found")
```
Register a soft (non-raising) error
```python
no.likey(1001, "Minor warning", soften=True)
```
Basic Usage
-----------

1) Raising an exception (outside any existing exception):
```python
try:
    no(404)

except no.way as noexcept:
    print(str(noexcept))

    # [404]
    # Resource not found
```
2) Attaching to an existing exception (inside an except block):
```python
try:
    risky_operation()

except ValueError as ve:
    # Wrap the ValueError in a new no.way with code 500
    no(500, ve)
```
This will raise a no.way whose complaint includes both [500] and the original ValueError context

3) Adding extra custom complaints:
```python
try:
    no(404, complaint="User ID 123 not found")

except no.way as noexcept:
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
  You can inspect `.codes` and `.linked` attributes on a caught `no.way` to see all accumulated codes and wrapped exceptions.
```python
try:
    no(404)

except no.way as noexcept:
    print(noexcept.nos)  # {404: ["Resource not found"]}
    print(noexcept.linked)  # {} (no linked exceptions)
    no(500, "Server error")
```
or even interrogate via if statements:
```python
try:
    no(404)

except no.way as noexcept:
    if 404 in noexcept.nos:
        print("404 detected in codes")
```

See the project README for more examples and the full API reference.
"""
class NoModule:
    way: type["NoBaseException"]
    hideTraceback: bool = False
    pending: RMBlock[Optional["NoBaseException"]]
    
    def __init__(self):
        self._registry: RMDict[int, Tuple[str, str, List[int], bool]] = RMDict("registry")
        self.pending: RMBlock[Optional[NoBaseException]] = RMBlock("nopending", BlockSize.s4096)  # Using DEFAULT_BLOCK_SIZE equivalent
        self.pending.value = None
        self._lock = threading.Lock()
        # Thread-local storage for pending exceptions
        self._thread_local = threading.local()

    def go(
        self,
        code: int,
        fn: Optional[Callable[..., T]] = None,
        *args: Any,
        soften: bool = False,
        **kwargs: Any
    ) -> Any:
        """
        If called as go(code, fn, *args, soften=False, **kwargs):
            runs fn(*args, **kwargs), links & (soft-)raises on exception.

        If used as a context manager:
            with no.go(code, soften=False):
                <any code>
            links & suppresses any exception in the block under `code`.
        """
        # Callable‐invocation path
        if fn is not None:
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                # propagate if the failure is already a no.way
                if isinstance(exc, NoBaseException):
                    # add the new code to the existing exception
                    self(code, soften=soften)
                else:
                    # record under `code`, swallow or re-raise based on soften
                    self(code, exc, soften=soften)
                return None

        # Context-manager path
        @contextmanager
        def _ctx():
            try:
                yield
            except Exception as exc:
                if isinstance(exc, NoBaseException):
                    self(code, soften=soften)
                else:
                    # record & swallow
                    self(code, exc, soften=soften)
        return _ctx()
    
    def dice(self) -> None:
        """
        "No dice": wipe out any pending exception and its accumulated codes/messages.
        
        This clears both thread-local and global pending exceptions, resetting the state
        to a clean slate. After this call:
        - no.bueno returns False
        - no.nos returns an empty dict
        - no.complaints returns an empty list
        
        This is useful for cleaning up state between tests or after handling a batch
        of soft exceptions.
        """
        self.pending.value = None
        # Clear thread-local pending as well
        if hasattr(self._thread_local, 'pending'):
            self._thread_local.pending = None
        
    def traceback(self) -> None:
        """
        Hide the traceback when raising exceptions.
        
        When called, this sets the hideTraceback flag which causes exceptions
        to be printed to stdout and the program to exit with code 1, rather
        than raising the exception normally with a full traceback.
        
        This is useful for production environments where you want cleaner
        error output without the full Python stack trace.
        """
        self.hideTraceback = True

    @property
    def bueno(self) -> bool:
        """
        Returns true if there is a pending or an active no.way
        """
        # Check thread-local pending first, then global pending
        return (getattr(self._thread_local, 'pending', None) is not None or 
                self.pending.value is not None)

    @property
    def complaints(self) -> list[str]:
        """
        If there's a pending "cry-now" exception, return its flattened messages.
        Otherwise, if you're inside an except block catching a NoBaseException,
        return that exception's messages.  Failing both, return an empty list.
        """
        # 1) Check thread-local first, then global pending
        stash = getattr(self._thread_local, 'pending', None) or self.pending.value
        if stash is None:
            # 2) Fallback to currently-caught NoBaseException
            import sys
            _, baseException, _ = sys.exc_info()
            if isinstance(baseException, NoBaseException):
                stash = baseException

        if not stash:
            return []

        # Flatten all the per-code message lists
        msgs: list[str] = []
        for m_list in stash.nos.values():
            msgs.extend(m_list)
        return msgs
    
    @property
    def nos(self) -> Dict[int, List[str]]:
        """
        If there's a pending "cry-now" exception, return its codes.
        Otherwise, if you're inside an except block catching a NoBaseException,
        return that exception's codes.  Failing both, return an empty dict.
        """
        # 1) Check thread-local first, then global pending
        stash = getattr(self._thread_local, 'pending', None) or self.pending.value
        if stash is not None:
            return cast(NoBaseException, stash).nos

        # 2) Fallback to the currently caught NoBaseException
        import sys
        _, noBaseError, _ = sys.exc_info()
        if isinstance(noBaseError, NoBaseException):
            return noBaseError.nos

        # 3) Nothing active
        return {}

    @overload
    def likey(self, code: int, defaultComplaint: str) -> None: ...
    @overload
    def likey(self, code: int, defaultComplaint: str, *, soft: bool) -> None: ...
    @overload
    def likey(self, code: int, defaultComplaint: str, linkedCodes: Optional[List[int]]) -> None: ...
    @overload
    def likey(self, code: int, defaultComplaint: str, linkedCodes: Optional[List[int]], *, soft:bool) -> None: ...

    def likey(
        self,
        code: int,
        defaultComplaint: str = "",
        linkedCodes: Optional[List[int]] = None,
        *,
        soft: bool = False
    ) -> None:
        """
        Register a new error code with the noexcept module.

        This creates a new subclass of `NoBaseException` named `Error{code}`, makes it
        available as an attribute on the module (e.g. `no.Error404`), and stores its
        default complaint, any linked codes, and soft-flag in the registry.

        Parameters
        ----------
        code : int
            Numeric identifier for the error. This is the value you pass to `no(code)`
            to raise or reference this exception.

        defaultComplaint : str, optional
            Human-readable default complaint for this code. If omitted or empty,
            a generic `"Error {code}"` complaint will be used.

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

        no.likey(404, "Not Found")

        try:
            no(404)

        except no.way as noexcept:
            print(noexcept)

            [404]
            Not Found
        ```
        2) Soft registration (accumulate without raising):
        ```python
        no.likey(1001, "Minor warning", soft=True)

        no(1001)      # no exception is thrown immediately
        ```
        3) Registration with linked codes:
        ```python
        no.likey(500, "Server Error", linkedCodes=[404, 403])

        try:
            no(500)

        except no.way as noexcept:
            print(noexcept.nos)

            [500, 404, 403]
        ```
        4) Using the generated exception subclass directly:
        ```python
        raise no.Error500("Custom override complaint")
        ```
        """
        # Prepare data outside the lock to minimize lock time
        name = f"Error{code}"
        excType = type(name, (NoBaseException,), {})
        registry_entry = (
            name,
            defaultComplaint or f"Error {code}",
            linkedCodes or [],
            soft
        )
        
        # Critical section - minimize time holding lock
        with self._lock:
            # Check if already registered to avoid duplicates
            if code in self._registry:
                return
            
            setattr(self, name, excType)
            setattr(sys.modules[__name__], name, excType)
            self._registry[code] = registry_entry

    @overload
    def __call__(self, soften: bool = False) -> None: ...
    @overload
    def __call__(self, exception: BaseException, *, complaint: str = "", soften: bool = False) -> None: ...
    @overload
    def __call__(self, code: int, *, complaint: str = "", soften: bool = False) -> None: ...
    @overload
    def __call__(self, code: int, msg: str, *, soften: bool = False) -> None: ...
    @overload
    def __call__(self, code: int, exception: BaseException, *, soften: bool = False) -> None: ...
    @overload
    def __call__(self, codes: List[int], *, complaint: str = "", linked: Optional[List[BaseException]] = None, soften: bool = False) -> None: ...

    def __call__(self, *args, **kwargs) -> None:
        from .call import _handleCall
        return _handleCall(self, True, *args, **kwargs)

    def _makeOne(
        self,
        code: int,
        complaint: Optional[str],
        linked: Optional[List[BaseException]]
    ) -> NoBaseException:
        with self._lock:
            excName, defaultMsg, linkedCodes, softFlag = self._registry.get(
                code, ("NoBaseException", f"Error {code}", [], False)
            )

        if excName == "NoBaseException":
            excType = NoBaseException
        else:
            excType = getattr(sys.modules[__name__], excName, None)
            if excType is None:
                excType = type(excName, (NoBaseException,), {})
                setattr(sys.modules[__name__], excName, excType)
                setattr(self, excName, excType)

        softCodes = {code: softFlag}
        exc = excType(code, complaint, defaultComplaint=defaultMsg, linked={}, softCodes=softCodes)
        if linked:
            for l in linked:
                exc._recordLinkedException(l)
        for extra in linkedCodes:
            msg = self._registry.get(extra, (None, f"Error {extra}", [], False))[1]
            extraSoft = self._registry.get(extra, (None, "", [], False))[3]
            exc.addCode(extra, msg)
            exc._softCodes[extra] = extraSoft
        return exc

    def propagate(self, exc: NoBaseException, newCode: int) -> None:
        """
        Add a new error code to an existing NoBaseException.
        
        This method is used internally to propagate error codes when one exception
        is being wrapped or extended with additional error information.
        
        Parameters
        ----------
        exc : NoBaseException
            The existing exception to add the code to
        newCode : int
            The error code to add
        """
        msg = self._registry.get(newCode, (None, f"Error {newCode}", [], False))[1]
        soft = self._registry.get(newCode, (None, "", [], False))[3]
        exc.addCode(newCode, msg)
        exc._softCodes[newCode] = soft

    def understand(self, lang: str) -> None:
        """
        Language support is not implemented yet.
        """
        raise NotImplementedError("Language support not implemented yet.")
    
    def build(self) -> NoBuilder:
        """
        Create a new exception builder for complex exception creation.
        
        Example:
        --------
        exc = no.build().withCode(404, "Not Found").withCode(500, "Server Error").asSoft(404).build()
        """
        return NoBuilder()
    

no = NoModule()
no.way = NoBaseException

__all__ = ["no"]