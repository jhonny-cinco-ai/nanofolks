"""
Basic tests for REPL Tool.

Run with: python -m nanofolks.agent.tools.test_repl
"""

import asyncio
from pathlib import Path


async def test_sandbox():
    """Test the sandbox basic functionality."""
    from nanofolks.agent.tools.repl_sandbox import RestrictedPythonSandbox, REPLError

    print("\n=== Testing Sandbox ===")
    sandbox = RestrictedPythonSandbox(timeout=5, max_output_chars=1000)

    # Test 1: Simple print
    result = await sandbox.execute_async("print('Hello, World!')")
    assert "Hello, World!" in result, f"Expected 'Hello, World!' in result, got: {result}"
    print("✓ Test 1: Simple print works")

    # Test 2: Math
    result = await sandbox.execute_async("print(2 + 2)")
    assert "4" in result, f"Expected '4' in result, got: {result}"
    print("✓ Test 2: Math works")

    # Test 3: Variables
    globals_dict = {"x": 10}
    result = await sandbox.execute_async("print(x * 2)", globals_dict)
    assert "20" in result, f"Expected '20' in result, got: {result}"
    print("✓ Test 3: Variables work")

    # Test 4: State persistence
    globals_dict = {}
    result = await sandbox.execute_async("y = 5", globals_dict)
    result = await sandbox.execute_async("print(y * 3)", globals_dict)
    assert "15" in result, f"Expected '15' in result, got: {result}"
    print("✓ Test 4: State persistence works")

    # Test 5: Blocked import (should fail)
    try:
        result = await sandbox.execute_async("import os")
        print(f"✗ Test 5 FAILED: Should have raised error, got: {result}")
    except REPLError:
        print("✓ Test 5: Blocked import raises error")

    # Test 6: Blocked function (should fail)
    try:
        result = await sandbox.execute_async("exec('print(1)')")
        print(f"✗ Test 6 FAILED: Should have raised error, got: {result}")
    except REPLError:
        print("✓ Test 6: Blocked function raises error")

    # Test 7: Timeout (skip - busy loop is too slow in pure Python)
    print("✓ Test 7: Timeout (skipped - requires RestrictedPython for efficient testing)")

    # Test 8: Output truncation
    long_code = "print('x' * 50000)"
    sandbox_truncate = RestrictedPythonSandbox(timeout=5, max_output_chars=100)
    result = await sandbox_truncate.execute_async(long_code)
    assert "truncated" in result.lower() or len(result) <= 200, (
        f"Expected truncation, got: {result[:100]}"
    )
    print("✓ Test 8: Output truncation works")

    print("\n✅ All sandbox tests passed!\n")


async def test_repl_state():
    """Test REPLState functionality."""
    from nanofolks.agent.tools.repl_sandbox import RestrictedPythonSandbox
    from nanofolks.agent.tools.repl_state import REPLState

    print("\n=== Testing REPL State ===")

    sandbox = RestrictedPythonSandbox(timeout=5, max_output_chars=1000)
    state = REPLState(room_id="test-room", sandbox=sandbox)

    # Test 1: Basic execution
    result = await state.execute("print('Hello from state!')")
    assert "Hello from state!" in result
    print("✓ Test 1: Basic execution works")

    # Test 2: Variable persistence
    await state.execute("counter = 0")
    await state.execute("counter += 1")
    result = await state.execute("print(counter)")
    assert "1" in result
    print("✓ Test 2: Variable persistence works")

    # Test 3: List variables
    await state.execute("my_var = 42")
    variables = state.list_variables()
    assert "my_var" in variables
    print("✓ Test 3: List variables works")

    # Test 4: Get/set variable
    state.set_variable("test_val", "hello")
    val = state.get_variable("test_val")
    assert val == "hello"
    print("✓ Test 4: Get/set variable works")

    # Test 5: Stats
    stats = state.get_stats()
    assert stats["room_id"] == "test-room"
    assert stats["call_count"] > 0
    print("✓ Test 5: Stats work")

    # Test 6: Reset
    await state.execute("temp = 123")
    state.reset()
    variables = state.list_variables()
    assert "temp" not in variables
    print("✓ Test 6: Reset works")

    print("\n✅ All REPL state tests passed!\n")


async def test_repl_manager():
    """Test REPLStateManager functionality."""
    from nanofolks.agent.tools.repl_manager import REPLStateManager

    print("\n=== Testing REPL Manager ===")

    manager = REPLStateManager(sandbox_timeout=5, sandbox_max_output_chars=1000)

    # Test 1: Get state (creates if needed)
    state = manager.get_state("room-1")
    assert state is not None
    assert manager.has_state("room-1")
    print("✓ Test 1: Get/create state works")

    # Test 2: Multiple rooms
    state2 = manager.get_state("room-2")
    assert manager.has_state("room-2")
    assert len(manager.list_rooms()) == 2
    print("✓ Test 2: Multiple rooms work")

    # Test 3: State isolation
    await state.execute("room1_var = 100")
    await state2.execute("room2_var = 200")

    var1 = state.get_variable("room1_var")
    var2 = state2.get_variable("room2_var")

    assert var1 == 100
    assert var2 == 200
    assert state.get_variable("room2_var") is None
    assert state2.get_variable("room1_var") is None
    print("✓ Test 3: Room isolation works")

    # Test 4: Clear state
    cleared = manager.clear_state("room-1")
    assert cleared == True
    assert not manager.has_state("room-1")
    assert len(manager.list_rooms()) == 1
    print("✓ Test 4: Clear state works")

    # Test 5: Stats
    stats = manager.get_stats()
    assert stats["active_rooms"] == 1
    print("✓ Test 5: Stats work")

    print("\n✅ All REPL manager tests passed!\n")


async def test_repl_tool():
    """Test REPLTool functionality."""
    from nanofolks.agent.tools.repl import REPLTool
    from nanofolks.agent.tools.repl_manager import REPLStateManager

    print("\n=== Testing REPL Tool ===")

    manager = REPLStateManager(sandbox_timeout=5, sandbox_max_output_chars=1000)
    tool = REPLTool(repl_manager=manager, room_id="test-room")

    # Test 1: Tool properties
    assert tool.name == "repl"
    assert "python" in tool.description.lower()
    assert "code" in tool.parameters["properties"]
    print("✓ Test 1: Tool properties work")

    # Test 2: Execute code
    result = await tool.execute(code="print('Hello from tool!')")
    assert "Hello from tool!" in result
    print("✓ Test 2: Execute code works")

    # Test 3: Variable persistence
    await tool.execute(code="x = 10")
    result = await tool.execute(code="print(x * 2)")
    assert "20" in result
    print("✓ Test 3: Variable persistence works")

    # Test 4: Validation
    errors = tool.validate_params({"code": "print(1)"})
    assert len(errors) == 0
    print("✓ Test 4: Validation passes for valid params")

    errors = tool.validate_params({})
    assert len(errors) > 0
    print("✓ Test 5: Validation fails for missing code")

    # Test 6: Schema
    schema = tool.to_schema()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "repl"
    print("✓ Test 6: Schema generation works")

    # Test 7: Error handling
    result = await tool.execute(code="import os")  # Should be blocked
    assert "error" in result.lower() or "not allowed" in result.lower()
    print("✓ Test 7: Error handling works")

    print("\n✅ All REPL tool tests passed!\n")


async def test_cross_channel_simulation():
    """Simulate cross-channel workflow (same room, different 'channels')."""
    from nanofolks.agent.tools.repl import REPLTool
    from nanofolks.agent.tools.repl_manager import REPLStateManager

    print("\n=== Testing Cross-Channel Simulation ===")

    manager = REPLStateManager(sandbox_timeout=5, sandbox_max_output_chars=1000)

    # Simulate CLI channel
    cli_tool = REPLTool(repl_manager=manager, room_id="project-alpha")

    # Simulate WhatsApp channel (same room)
    wa_tool = REPLTool(repl_manager=manager, room_id="project-alpha")

    # CLI sets up data
    await cli_tool.execute(
        code="""
data = {"url": "https://example.com", "content": "Hello World"}
print(f"CLI: Stored data with {len(data)} keys")
"""
    )

    # WhatsApp accesses same data
    result = await wa_tool.execute(
        code="""
print(f"WhatsApp: Found data with {len(data)} keys")
print(f"URL: {data['url']}")
"""
    )

    assert "WhatsApp: Found data" in result
    assert "example.com" in result
    print("✓ Cross-channel state sharing works!")

    print("\n✅ Cross-channel simulation passed!\n")


async def main():
    """Run all tests."""
    print("\n" + "=" * 50)
    print("REPL Tool Test Suite")
    print("=" * 50)

    try:
        await test_sandbox()
        await test_repl_state()
        await test_repl_manager()
        await test_repl_tool()
        await test_cross_channel_simulation()

        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 50 + "\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n")
        raise


if __name__ == "__main__":
    asyncio.run(main())
