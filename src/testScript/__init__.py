import os
import threading
from multiprocessing import Process
from noexcept import no
import traceback

results: dict[str, bool] = {}

def record(testName: str, func):
    try:
        func()
        results[testName] = True
    except Exception:
        print(f"Test {testName} failed:\n{traceback.format_exc()}")
        results[testName] = False

def testImportNo():
    try:
        no(404)
    except no.way as noexcept:
        assert 404 in noexcept.nos
        # Demonstrate explicit membership check
        if 404 in noexcept.nos:
            print("404 detected in codes")

def testSoftCode():
    no(123)  # Should not raise because 123 was registered soft

def testPropagation():
    try:
        no(404)
    except no.way as noexcept:
        no(500, soften=True)
        assert 404 in noexcept.nos and 500 in noexcept.nos

def testLinking():
    try:
        raise ValueError("bad")
    except ValueError as err:
        no(err)
        try:
            no(404, err)
        except no.way as noexcept:
            assert any("ValueError" in str(linked) for linked in noexcept.linked)

def testExceptionGroup():
    try:
        no([404, 500])
    except ExceptionGroup as eg:
        assert any(isinstance(exc, no.way) for exc in eg.exceptions)

def testStrOutput():
    try:
        no(404)
    except no.way as noexcept:
        s = str(noexcept)
        assert "404" in s and "Not Found" in s

def testUnregistered():
    try:
        no(999)
    except no.way as noexcept:
        assert 999 in noexcept.nos

def testMultipleMessages():
    no.likey(700, "Base Message")
    try:
        no(700, "Extra complaint")
    except no.way as noexcept:
        no(700, "Another", soften=True)
        assert any("Extra" in m for m in noexcept.complaints)
        assert any("Another" in m for m in noexcept.complaints)
        
def testCryNowRaiseLater():
    try:
        cryNowRaiseLater()
    except no.way:
        assert 600 in no.nos
        assert 666 in no.nos
        assert 667 in no.nos
        assert "Immediate failure" in no.complaints
        assert "Deferred failure" in no.nos[667]

def testGoCallable():
    # clear any leftover state
    no.dice()

    # good function returns a value
    def good_fn():
        return "success"
    result = no.go(800, good_fn)
    assert result == "success"
    assert not no.bueno
    assert no.nos == {}

    # bad function raises, swallowed with soften=True
    def bad_fn():
        raise RuntimeError("boom")
    result2 = no.go(801, bad_fn, soften=True)
    assert result2 is None
    assert 801 in no.nos

def testGoContextManager():
    # clear state
    no.dice()

    # any exception in the with-block gets swallowed & recorded
    with no.go(802, soften=True):
        raise KeyError("ctx error")
    assert 802 in no.nos

def cryNowRaiseLater():
    try:
        thereIsNoTry()  # type: ignore[no-untyped-call]
    except Exception as exception:
        no(600, exception)
        no(666, complaint="Immediate failure")
        no(667, complaint="Deferred failure")
        no()

def testThreadSafety():
    # Pick a batch of distinct codes
    codes = list(range(1000, 1010))
    
    def worker(code):
        # each thread registers its own code
        no.likey(code, f"Thread-msg {code}")

    # Spawn threads
    threads = [threading.Thread(target=worker, args=(c,)) for c in codes]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # All codes should now be in the shared registry
    registry = no._registry  # wired to SharedMemoryBackend.get(...) :contentReference[oaicite:4]{index=4}
    for c in codes:
        assert c in registry, f"Code {c} missing from registry"
def worker(code):
    # each process registers its own code
    no.likey(code, f"Process-msg {code}")

def testMultiProcessingSafety():
    print("Testing multiprocessing safety...")
    # Pick a batch of distinct codes
    codes = list(range(2000, 2010))
    
    # Spawn processes
    processes = [Process(target=worker, args=(c,)) for c in codes]
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    
    # All codes should now be in the shared registry
    registry = no._registry  # wired to SharedMemoryBackend.get(...) :contentReference[oaicite:4]{index=4}
    for c in codes:
        assert c in registry, f"Code {c} missing from registry"

def main():
    print("Running no-exceptions self-test...")

    # Register required codes
    no.likey(404, "Not Found")
    no.likey(500, "Server Error")
    no.likey(123, "Soft Error", soft=True)
    no.likey(600, "Initial Error", soft=True)
    no.likey(666, "Evil error", soft=True)
    no.likey(667, "Neighbours of the Beast:", soft=True)

    # Register codes for go() tests
    no.likey(800, "Good Function")
    no.likey(801, "Bad Function", soft=True)
    no.likey(802, "Context Failure", soft=True)

    # Run tests
    print("Initial no.bueno Test", no.bueno)

    record("Module Import", testImportNo)
    record("Soft Code Call", testSoftCode)
    record("Adding Codes", testPropagation)
    record("Linking Exception", testLinking)
    record("Exception Groups", testExceptionGroup)
    record("Output", testStrOutput)
    record("Unregistered Code", testUnregistered)
    record("Multiple Complaints", testMultipleMessages)
    record("Cry Now, Raise Later", testCryNowRaiseLater)
    record("Go Callable", testGoCallable)
    record("Go Context Manager", testGoContextManager)
    record("Thread Safety", testThreadSafety)
    #record("Multi-Processing Safety", testMultiProcessingSafety)

    print("Final no.bueno Test", no.bueno)

    print("\nTest summary:")
    for name, ok in results.items():
        print(f" - {name}: {'PASS' if ok else 'FAIL'}")

    if not all(results.values()):
        raise SystemExit(1)

    print("All tests passed!")
    no.dice()  # Clear state after tests