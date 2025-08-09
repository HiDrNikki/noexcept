from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple, overload
from collections import defaultdict
import io
import weakref

class NoBaseException(Exception):
    __slots__ = ('nos', '_softCodes', 'linked', '_nos_defaultdict', '_linked_defaultdict')
    nos: Dict[int, List[str]]
    """
    Base class for all exceptions raised by the noexcept module.

    Attributes
    ----------
    codes : List[int]
        The numeric error codes attached to this exception (in order of registration or propagation).

    complaints : List[str]
        The default and any appended custom complaints for each code in `codes`.

    linked : List[Exception]
        Any underlying exceptions that have been linked into this one (e.g. via propagation or direct linking).

    soften : bool
        If True, this code was registered or called in “soft” mode and won't automatically raise when invoked.

    Usage
    -----
    1. Raising directly via `no()` or instantiating yourself:
    ```python
    import no

    no.likey(404, "Not Found")

    try:
        no(404)

    except no.way as noexcept:
        print(noexcept.nos)

        # [404]
        # Not Found
    ```
    2. Inspecting codes, complaints, and linked exceptions:
    ```python
    try:
        no(403)

    except no.way as noexcept:
        print(noexcept.nos)      # [403]
        print(noexcept.complaints)   # ["Forbidden"] (assuming you registered 403 → "Forbidden")
    ```
    3. Chaining an existing exception:
    ```python
    try:
        raise KeyError("missing key")

    except KeyError as ke:
        no(500, ke)  # wraps KeyError under code 500

        Traceback (most recent call last):
                ...
            no.way: [500]
            Server error
            └─ linked KeyError: 'missing key'
    ```
    The original KeyError appears in `noexcept.linked`.
    """
    @property
    def complaints(self) -> List[str]:
        """
        Returns a flattened list of all complaints associated with this exception.
        This includes the default complaint for each code and any custom messages added.
        """
        return [complaint for complaints in self.nos.values() for complaint in complaints]
    
    def __init__(
        self,
        code: int,
        complaint: Optional[str] = None,
        codes: Optional[Dict[int, List[str]]] = None,
        linked: Optional[
            Dict[Tuple[type, str], Set[Tuple[Optional[str], Optional[int]]]]
        ] = None,
        defaultComplaint: Optional[str] = None,
        softCodes: Optional[Dict[int, bool]] = None
    ):
        self.nos: Dict[int, List[str]] = {} if codes is None else codes
        if code not in self.nos:
            self.nos[code] = [defaultComplaint or f"Error {code}"]
        if complaint:
            self.nos[code].append(complaint)

        self._softCodes: Dict[int, bool] = {} if softCodes is None else softCodes
        self.linked: Dict[Tuple[type, str], Set[Tuple[Optional[str], Optional[int]]]] = (
            {} if linked is None else linked
        )

        super().__init__(self._composeText())

    def _composeText(self) -> str:
        output = io.StringIO()
        output.write(f"[{','.join(map(str, self.nos.keys()))}]")
        for code, msgs in self.nos.items():
            for msg in msgs:
                output.write(f"\n{msg}")
        return output.getvalue()

    def addMessage(self, code: int, complaint: Optional[str]) -> None:
        if complaint:
            if not hasattr(self, '_nos_defaultdict'):
                self._nos_defaultdict = defaultdict(list, self.nos)
            self._nos_defaultdict[code].append(complaint)
            self.nos = dict(self._nos_defaultdict)

    def addCode(self, code: int, defaultComplaint: Optional[str] = None) -> None:
        if code not in self.nos:
            self.nos[code] = [defaultComplaint or f"Error {code}"]

    def _recordLinkedException(self, exception: BaseException) -> None:
        # Use weak reference to prevent circular references
        try:
            weak_exc = weakref.ref(exception)
            key = (type(exception), str(exception))
        except TypeError:
            # Some objects cannot be weakly referenced, fall back to strong reference
            key = (type(exception), str(exception))
            
        traceback = exception.__traceback__
        if traceback:
            while traceback.tb_next:
                traceback = traceback.tb_next
            loc = (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno)
        else:
            loc = (None, None)
        if not hasattr(self, '_linked_defaultdict'):
            self._linked_defaultdict = defaultdict(set, self.linked)
        self._linked_defaultdict[key].add(loc)
        self.linked = dict(self._linked_defaultdict)

    @overload
    def __call__(self, soften: bool = False) -> None: ...
    @overload
    def __call__(self, exception: BaseException, *, complaint: str = "", soften: bool = False) -> None: ...
    @overload
    def __call__(self, code: int, *, complaint: str = "", soften: bool = False) -> None: ...
    @overload
    def __call__(self, code: int, complaint: str, *, soften: bool = False) -> None: ...
    @overload
    def __call__(self, code: int, exception: BaseException, *, soften: bool = False) -> None: ...
    @overload
    def __call__(self, codes: List[int], *, complaint: str = "", linked: Optional[List[BaseException]] = None, soften: bool = False) -> None: ...

    def __call__(self, *args, **kwargs) -> None:
        from .call import _handleCall
        return _handleCall(self, False, *args, **kwargs)

class NoBuilder:
    """Builder pattern for creating complex exceptions with multiple codes and linked exceptions"""
    
    def __init__(self):
        self._codes: Dict[int, List[str]] = {}
        self._linked: List[BaseException] = []
        self._soft_codes: Dict[int, bool] = {}
    
    def withCode(self, code: int, complaint: Optional[str] = None) -> 'NoBuilder':
        """Add a code with optional complaint"""
        if code not in self._codes:
            self._codes[code] = []
        if complaint:
            self._codes[code].append(complaint)
        return self
    
    def withLinked(self, exception: BaseException) -> 'NoBuilder':
        """Add a linked exception"""
        self._linked.append(exception)
        return self
    
    def asSoft(self, code: int) -> 'NoBuilder':
        """Mark a code as soft (non-raising)"""
        self._soft_codes[code] = True
        return self
    
    def build(self) -> NoBaseException:
        """Build the final exception"""
        if not self._codes:
            raise ValueError("At least one code must be specified")
        
        # Get the first code as the primary code
        primary_code = next(iter(self._codes.keys()))
        primary_complaints = self._codes[primary_code]
        primary_complaint = primary_complaints[0] if primary_complaints else None
        
        # Create the exception
        exc = NoBaseException(primary_code, primary_complaint, codes=self._codes.copy(), softCodes=self._soft_codes.copy())
        
        # Add linked exceptions
        for linked_exc in self._linked:
            exc._recordLinkedException(linked_exc)
        
        return exc

    def __str__(self) -> str:
        output = io.StringIO()
        output.write(f"[{','.join(map(str, self.nos.keys()))}]")
        
        for code, msgs in self.nos.items():
            for msg in msgs:
                output.write(f"\n{msg}")

        traceback = self.__traceback__
        if traceback:
            while traceback.tb_next:
                traceback = traceback.tb_next
            output.write(f"\nRaised at {traceback.tb_frame.f_code.co_filename}:{traceback.tb_lineno}")

        if self.__context__ is not None:
            output.write(f"\ncontext: {type(self.__context__).__name__}: {self.__context__}")
        if self.__cause__ is not None:
            output.write(f"\ncause: {type(self.__cause__).__name__}: {self.__cause__}")

        if self.linked:
            output.write("\nlinked:")
            for (exceptionType, msg), locations in self.linked.items():
                locationText = ", ".join(
                    f"{f}:{ln}" if f else "unknown" for f, ln in sorted(locations)
                )
                output.write(f"\n  {exceptionType.__name__}: {msg} @ {locationText}")

        return output.getvalue()
