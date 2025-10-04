from collections.abc import AsyncIterator
import inspect

import pytest

from admin.lib.messageStrategies import NoMessages


@pytest.mark.asyncio
async def test_no_messages_is_async_iterator() -> None:
    iterator = NoMessages()

    assert isinstance(iterator, AsyncIterator)
    assert inspect.isasyncgen(iterator)

    with pytest.raises(StopAsyncIteration):
        await iterator.__anext__()
