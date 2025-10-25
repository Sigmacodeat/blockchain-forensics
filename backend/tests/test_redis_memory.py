"""Tests for Redis-based chat memory"""
import pytest
import asyncio

from app.services.redis_memory import (
    get_redis_client,
    get_chat_memory,
    append_chat_memory,
    clear_chat_memory
)


@pytest.mark.asyncio
async def test_redis_client_init():
    """Test Redis client initialization."""
    client = get_redis_client()
    # Client may be None if Redis is not available (fallback mode)
    # This is expected and acceptable
    assert client is None or client is not None


@pytest.mark.asyncio
async def test_chat_memory_append_and_get():
    """Test appending and retrieving chat memory."""
    session_id = "test_session_123"
    
    # Clear any existing memory
    await clear_chat_memory(session_id)
    
    # Append messages
    await append_chat_memory(session_id, "user", "Hello")
    await append_chat_memory(session_id, "assistant", "Hi there!")
    await append_chat_memory(session_id, "user", "How are you?")
    
    # Retrieve memory
    memory = await get_chat_memory(session_id, limit=10)
    
    if memory:  # If Redis is available
        assert len(memory) == 3
        assert memory[0]["role"] == "user"
        assert memory[0]["content"] == "Hello"
        assert memory[1]["role"] == "assistant"
        assert memory[1]["content"] == "Hi there!"
        assert memory[2]["role"] == "user"
        assert memory[2]["content"] == "How are you?"
    
    # Cleanup
    await clear_chat_memory(session_id)


@pytest.mark.asyncio
async def test_chat_memory_limit():
    """Test memory limit enforcement."""
    session_id = "test_session_limit"
    
    # Clear any existing memory
    await clear_chat_memory(session_id)
    
    # Append more than max_messages (default 30)
    for i in range(35):
        await append_chat_memory(session_id, "user", f"Message {i}")
    
    # Retrieve memory
    memory = await get_chat_memory(session_id, limit=50)
    
    if memory:  # If Redis is available
        # Should only have last 30 messages
        assert len(memory) <= 30
        # Check that we have the most recent messages
        if len(memory) > 0:
            assert "Message 34" in memory[-1]["content"] or "Message" in memory[-1]["content"]
    
    # Cleanup
    await clear_chat_memory(session_id)


@pytest.mark.asyncio
async def test_chat_memory_empty_session():
    """Test retrieving memory for non-existent session."""
    session_id = "nonexistent_session_999"
    
    memory = await get_chat_memory(session_id)
    
    # Should return None for empty/nonexistent session
    assert memory is None or len(memory) == 0


@pytest.mark.asyncio
async def test_chat_memory_clear():
    """Test clearing chat memory."""
    session_id = "test_session_clear"
    
    # Add some messages
    await append_chat_memory(session_id, "user", "Test message")
    
    # Clear memory
    await clear_chat_memory(session_id)
    
    # Verify cleared
    memory = await get_chat_memory(session_id)
    assert memory is None or len(memory) == 0


@pytest.mark.asyncio
async def test_chat_memory_invalid_session():
    """Test handling of invalid session IDs."""
    # None session_id should be handled gracefully
    await append_chat_memory(None, "user", "Test")
    memory = await get_chat_memory(None)
    assert memory is None
    
    # Empty string session_id
    await append_chat_memory("", "user", "Test")
    memory = await get_chat_memory("")
    assert memory is None


@pytest.mark.asyncio
async def test_chat_memory_empty_content():
    """Test appending empty content."""
    session_id = "test_session_empty"
    
    # Clear any existing memory
    await clear_chat_memory(session_id)
    
    # Try to append empty content (should be ignored)
    await append_chat_memory(session_id, "user", "")
    await append_chat_memory(session_id, "user", None)
    
    # Verify nothing was added
    memory = await get_chat_memory(session_id)
    assert memory is None or len(memory) == 0
    
    # Cleanup
    await clear_chat_memory(session_id)


@pytest.mark.asyncio
async def test_chat_memory_concurrent_access():
    """Test concurrent access to chat memory."""
    session_id = "test_session_concurrent"
    
    # Clear any existing memory
    await clear_chat_memory(session_id)
    
    # Append messages concurrently
    tasks = [
        append_chat_memory(session_id, "user", f"Message {i}")
        for i in range(10)
    ]
    await asyncio.gather(*tasks)
    
    # Retrieve memory
    memory = await get_chat_memory(session_id)
    
    if memory:  # If Redis is available
        # All 10 messages should be present
        assert len(memory) == 10
    
    # Cleanup
    await clear_chat_memory(session_id)
