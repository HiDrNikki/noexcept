from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple, overload

class NoBaseException(Exception):
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
        parts = [f"[{','.join(map(str, self.nos.keys()))}]"]
        for code, msgs in self.nos.items():
            parts.extend(msgs)
        return "\n".join(parts)

    def addMessage(self, code: int, complaint: Optional[str]) -> None:
        if complaint:
            self.nos.setdefault(code, []).append(complaint)

    def addCode(self, code: int, defaultComplaint: Optional[str] = None) -> None:
        if code not in self.nos:
            self.nos[code] = [defaultComplaint or f"Error {code}"]

    def _recordLinkedException(self, exception: BaseException) -> None:
        key = (type(exception), str(exception))
        traceback = exception.__traceback__
        if traceback:
            while traceback.tb_next:
                traceback = traceback.tb_next
            loc = (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno)
        else:
            loc = (None, None)
        self.linked.setdefault(key, set()).add(loc)

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

    def __str__(self) -> str:
        parts = [f"[{','.join(map(str, self.nos.keys()))}]"]
        for code, msgs in self.nos.items():
            parts.extend(msgs)

        traceback = self.__traceback__
        if traceback:
            while traceback.tb_next:
                traceback = traceback.tb_next
            parts.append(f"Raised at {traceback.tb_frame.f_code.co_filename}:{traceback.tb_lineno}")

        if self.__context__ is not None:
            parts.append(f"context: {type(self.__context__).__name__}: {self.__context__}")
        if self.__cause__ is not None:
            parts.append(f"cause: {type(self.__cause__).__name__}: {self.__cause__}")

        if self.linked:
            parts.append("linked:")
            for (exceptionType, msg), locations in self.linked.items():
                locationText = ", ".join(
                    f"{f}:{ln}" if f else "unknown" for f, ln in sorted(locations)
                )
                parts.append(f"  {exceptionType.__name__}: {msg} @ {locationText}")

        return "\n".join(parts)
