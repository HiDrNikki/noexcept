import traceback
from noexcept import no

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
    except no.xcpt as noexcept:
        assert 404 in noexcept.codes
        # Demonstrate explicit membership check
        if 404 in noexcept.codes:
            print("404 detected in codes")

def testSoftCode():
    no(123)  # Should not raise because 123 was registered soft

def testPropagation():
    try:
        no(404)
    except no.xcpt as noexcept:
        no(500, soften=True)
        assert 404 in noexcept.codes and 500 in noexcept.codes

def testLinking():
    try:
        raise ValueError("bad")
    except ValueError as err:
        no(err)
        try:
            no(404, err)
        except no.xcpt as noexcept:
            assert any("ValueError" in str(linked) for linked in noexcept.linked)

def testExceptionGroup():
    try:
        no([404, 500])
    except ExceptionGroup as eg:
        assert any(isinstance(exc, no.xcpt) for exc in eg.exceptions)

def testStrOutput():
    try:
        no(404)
    except no.xcpt as noexcept:
        s = str(noexcept)
        assert "404" in s and "Not Found" in s

def testUnregistered():
    try:
        no(999)
    except no.xcpt as noexcept:
        assert 999 in noexcept.codes

def testMultipleMessages():
    no.register(700, "Base Message")
    try:
        no(700, "Extra message")
    except no.xcpt as noexcept:
        no(700, "Another", soften=True)
        messages = noexcept.codes[700]
        assert any("Extra" in m for m in messages)
        assert any("Another" in m for m in messages)

def main():
    print("Running no-exceptions self-test...")

    # Register required codes
    no.register(404, "Not Found")
    no.register(500, "Server Error")
    no.register(123, "Soft Error", soft=True)

    # Run tests
    record("importNo", testImportNo)
    record("softCode", testSoftCode)
    record("propagation", testPropagation)
    record("linking", testLinking)
    record("exceptionGroup", testExceptionGroup)
    record("strOutput", testStrOutput)
    record("unregistered", testUnregistered)
    record("multipleMessages", testMultipleMessages)

    print("\nTest summary:")
    for name, ok in results.items():
        print(f" - {name}: {'OK' if ok else 'FAIL'}")

    if not all(results.values()):
        raise SystemExit(1)

    print("All tests passed!")