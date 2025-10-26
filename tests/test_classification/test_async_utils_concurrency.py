import asyncio
import pytest
from unittest.mock import AsyncMock
from catflap_prey_detector.classification.prey_detector_api.async_utils import (
    async_consumer_with_task_group_and_result_processor,
    async_consumer_queue
)
from catflap_prey_detector.detection.detection_result import DetectionResult


@pytest.fixture(autouse=True)
async def clear_queue():
    """Clear the queue before each test to avoid interference between tests."""
    while not async_consumer_queue.sync_q.empty():
        try:
            async_consumer_queue.sync_q.get_nowait()
        except Exception:
            break
    yield
    while not async_consumer_queue.sync_q.empty():
        try:
            async_consumer_queue.sync_q.get_nowait()
        except Exception:
            break


@pytest.mark.asyncio
async def test_concurrency_limit():
    """Test that the function properly limits concurrent executions to max_concurrent"""
    concurrent_count = 0
    max_concurrent_reached = 0
    
    async def mock_coroutine(item):
        nonlocal concurrent_count, max_concurrent_reached
        if item is None:
            return DetectionResult.negative()
        
        concurrent_count += 1
        max_concurrent_reached = max(max_concurrent_reached, concurrent_count)
        
        await asyncio.sleep(0.1)
        
        concurrent_count -= 1
        return DetectionResult.negative()
    
    trigger_mock = AsyncMock()
    
    for i in range(15): 
        async_consumer_queue.sync_q.put(f"item_{i}")
    
    async_consumer_queue.sync_q.put(None)
    
    await async_consumer_with_task_group_and_result_processor(
        mock_coroutine, 
        trigger_mock, 
        timeout_seconds=1.0,
        max_concurrent=5
    )
    
    assert max_concurrent_reached <= 5
    assert max_concurrent_reached > 0


@pytest.mark.asyncio
async def test_declining_excess_requests():
    """Test that excess requests are declined when max_concurrent is reached"""
    processed_count = 0
    declined_count = 0
    
    async def slow_coroutine(item):
        nonlocal processed_count, declined_count
        if item is None:
            declined_count += 1
            return DetectionResult.negative()
        
        processed_count += 1
        await asyncio.sleep(0.2)
        return DetectionResult.negative()
    
    trigger_mock = AsyncMock()
    
    for i in range(20):
        async_consumer_queue.sync_q.put(f"item_{i}")
    
    async_consumer_queue.sync_q.put(None)
    
    await async_consumer_with_task_group_and_result_processor(
        slow_coroutine,
        trigger_mock,
        timeout_seconds=1.0,
        max_concurrent=2
    )
    
    assert processed_count > 0
    assert processed_count < 20
    assert declined_count > 0


@pytest.mark.asyncio 
async def test_trigger_still_works_with_concurrency_limit():
    """Test that trigger function is still called when a coroutine returns positive result"""
    async def mock_coroutine(item):
        if item == "trigger_item":
            return DetectionResult.positive("result", b"data")
        return DetectionResult.negative()
    
    trigger_mock = AsyncMock()
    
    async_consumer_queue.sync_q.put("normal_item")
    async_consumer_queue.sync_q.put("trigger_item")
    async_consumer_queue.sync_q.put(None)
    
    await async_consumer_with_task_group_and_result_processor(
        mock_coroutine,
        trigger_mock,
        timeout_seconds=1.0,
        max_concurrent=5
    )
    
    trigger_mock.assert_called_once()
    call_args = trigger_mock.call_args[0][0]
    assert isinstance(call_args, list)
    assert len(call_args) == 2
    
    negative_results = [r for r in call_args if not r.is_positive]
    positive_results = [r for r in call_args if r.is_positive]
    
    assert len(negative_results) == 1
    assert len(positive_results) == 1
    assert positive_results[0].message == "result"
    assert positive_results[0].image_bytes == b"data"
