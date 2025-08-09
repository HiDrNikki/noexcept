import inspect
import sys
if sys.version_info >= (3, 11):
    # native PEP 654 support
    from builtins import ExceptionGroup
else:
    # backport installed via your env‑marker dependency
    from exceptiongroup import ExceptionGroup
from typing import Any, List, Optional, cast, Union, Tuple, Callable
from .module import no
from .exception import NoBaseException

def _getPending() -> Optional[NoBaseException]:
    """Get pending exception from thread-local or global storage"""
    thread_pending = getattr(no._thread_local, 'pending', None)
    return thread_pending or no.pending.value

def _setPending(exc: Optional[NoBaseException]) -> None:
    """Set pending exception to thread-local storage"""
    no._thread_local.pending = exc

def _getRegistryEntry(context: Union['NoModule', NoBaseException], code: int, isModule: bool) -> Tuple[bool, str]:
    """Get soft flag and default message for a code, caching the registry lookup"""
    if isModule:
        registry_entry = context._registry.get(code, (None, f"Error {code}", [], False))
        return registry_entry[3], registry_entry[1]
    else:
        return context._softCodes.get(code, False), f"Error {code}"

def _handleSoftOrRaise(exc: NoBaseException, softFlag: bool, soften: bool) -> None:
    """Handle soft exceptions or raise immediately"""
    if softFlag or soften:
        _setPending(exc)
        return
    if no.hideTraceback: 
        raze(exc)
    raise exc

def _handleEmptyCall(context: Union['NoModule', NoBaseException], isModule: bool) -> None:
    """0) EMPTY CALL: no args, no complaint, no soften"""
    pending = _getPending()
    if pending is not None:
        if no.hideTraceback: raze(pending)
        raise pending
    
    if isModule:
        exception = context._makeOne(0, None, [])
        if no.hideTraceback: raze(exception)
        raise exception
    
    if no.hideTraceback: raze(context)
    raise context


def _handleExceptionGroup(context: Union['NoModule', NoBaseException], isModule: bool, codes: List[int], complaint: Optional[str]) -> None:
    """1) EXCEPTION GROUP: single list-of-codes arg"""
    if isModule:
        exceptions = [context._makeOne(c, complaint, []) for c in codes]
    else:
        exceptions = [context.__class__(c, complaint) for c in codes]
        if no.hideTraceback: raze(exceptions[0])
    raise ExceptionGroup("Multiple errors", exceptions)


def _handleSingleCode(
    context: Union['NoModule', NoBaseException],
    isModule: bool,
    code: int,
    complaint: Optional[str],
    soften: bool,
    exception: Optional[BaseException],
    traceback: Optional[Any]
) -> None:
    """3) SINGLE-CODE CALL: no(code)"""
    # Cache registry lookup for this code
    softFlag, defaultMsg = _getRegistryEntry(context, code, isModule)
    # 3a) EARLY ACCUMULATION
    if _getPending() is not None:
        pending = cast(NoBaseException, _getPending())
        pending.addCode(code, defaultMsg)
        if complaint:
            pending.addMessage(code, complaint)
        pending._softCodes[code] = softFlag
        # re-save pending to ensure modifications persist
        _setPending(pending)
        return
    # 3b) MODULE-PROPAGATION
    if isModule and isinstance(exception, NoBaseException):
        e = exception  # type: NoBaseException
        context.propagate(e, code)
        if complaint:
            e.addMessage(code, complaint)
        e._softCodes[code] = softFlag
        _handleSoftOrRaise(e, softFlag, soften)
    # 3c) INSTANCE-PROPAGATION
    if not isModule and isinstance(context, NoBaseException):
        context.addCode(code, defaultMsg)
        if complaint:
            context.addMessage(code, complaint)
        context._softCodes[code] = softFlag
        _handleSoftOrRaise(context, softFlag, soften)
    # 3d) FRESH NEW EXCEPTION
    exc = (
        context._makeOne(code, complaint, [])
        if isModule
        else context.__class__(code, complaint)
    )
    _handleSoftOrRaise(exc, softFlag, soften)


def _handleCodeExceptionLink(
    context: Union['NoModule', NoBaseException],
    isModule: bool,
    code: int,
    exception: BaseException,
    complaint: Optional[str],
    soften: bool,
    traceback: Optional[Any]
) -> None:
    """4) CODE+EXCEPTION LINK: no(code, exc)"""
    # Cache registry lookup for this code
    softFlag, defaultMsg = _getRegistryEntry(context, code, isModule)

    if isModule:
        exc = context._makeOne(code, complaint, [exception])
        _handleSoftOrRaise(exc, softFlag, soften)
    else:
        context.addCode(code, defaultMsg)
        context._recordLinkedException(exception)
        _handleSoftOrRaise(context, softFlag, soften)


def _handleCodeMessage(
    context: Union['NoModule', NoBaseException],
    isModule: bool,
    code: int,
    complaint: str,
    soften: bool,
    traceback: Optional[Any]
) -> None:
    """5) CODE+MESSAGE: no(code, custom_msg)"""
    # Cache registry lookup for this code
    softFlag, defaultMsg = _getRegistryEntry(context, code, isModule)
    if _getPending() is not None:
        pending = cast(NoBaseException, _getPending())
        pending.addCode(code, defaultMsg)
        pending.addMessage(code, complaint)
        pending._softCodes[code] = softFlag
        # persist updated pending block
        _setPending(pending)
        return
    if not isModule and isinstance(context, NoBaseException):
        context.addCode(code, defaultMsg)
        context.addMessage(code, complaint)
        context._softCodes[code] = softFlag
        _handleSoftOrRaise(context, softFlag, soften)
    exc = (
        context._makeOne(code, complaint, [])
        if isModule
        else context.__class__(code, complaint)
    )
    _handleSoftOrRaise(exc, softFlag, soften)


CallHandler = Callable[[Union['NoModule', NoBaseException], bool, ...], None]

# Strategy pattern: map argument patterns to handler functions
CALL_HANDLERS: List[Tuple[Callable[[Tuple[Any, ...]], bool], CallHandler]] = [
    # Pattern checker, handler function
    (lambda args: not args, lambda ctx, is_mod, *args, **kwargs: _handleEmptyCall(ctx, is_mod)),
    (lambda args: len(args) == 1 and isinstance(args[0], list), 
     lambda ctx, is_mod, *args, **kwargs: _handleExceptionGroup(ctx, is_mod, args[0], kwargs.get('complaint'))),
    (lambda args: len(args) == 1 and isinstance(args[0], BaseException), 
     lambda ctx, is_mod, *args, **kwargs: None),  # noop
    (lambda args: len(args) == 1 and isinstance(args[0], int), 
     lambda ctx, is_mod, *args, **kwargs: _handleSingleCode(ctx, is_mod, args[0], kwargs.get('complaint'), kwargs.get('soften', False), None, None)),
    (lambda args: len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], BaseException), 
     lambda ctx, is_mod, *args, **kwargs: _handleCodeExceptionLink(ctx, is_mod, args[0], args[1], kwargs.get('complaint'), kwargs.get('soften', False), None)),
    (lambda args: len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], str), 
     lambda ctx, is_mod, *args, **kwargs: _handleCodeMessage(ctx, is_mod, args[0], args[1], kwargs.get('soften', False), None)),
]

def _handleCall(
    context: Union['NoModule', NoBaseException], 
    isModule: bool, 
    *args: Union[int, str, List[int], BaseException], 
    complaint: Optional[str] = None, 
    soften: bool = False
) -> None:
    """Router for no() calls using strategy pattern"""
    # Check if this is an empty call with no params
    if not args and complaint is None and not soften:
        return _handleEmptyCall(context, isModule)
    
    # Try each handler pattern
    for pattern_checker, handler in CALL_HANDLERS:
        if pattern_checker(args):
            return handler(context, isModule, *args, complaint=complaint, soften=soften)
    
    # No pattern matched - provide helpful error
    valid_patterns = [
        "no() - empty call to raise pending exception",
        "no(code: int) - raise exception with error code",
        "no([code1, code2, ...]) - raise ExceptionGroup with multiple codes",
        "no(code: int, complaint: str) - raise with custom message",
        "no(code: int, exception: BaseException) - link existing exception",
        "no(exception: BaseException) - noop for raw exceptions"
    ]
    raise TypeError(f"Unsupported arguments for no(): {args}\n\nValid patterns:\n" + 
                   "\n".join(f"  - {pattern}" for pattern in valid_patterns))

def raze(exception: NoBaseException) -> None:
    """Raise the no.way."""
    print(exception)
    sys.exit(1)