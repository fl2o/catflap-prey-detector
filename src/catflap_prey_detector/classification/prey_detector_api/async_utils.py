import logging
import asyncio
from collections.abc import Callable
import culsans

logger = logging.getLogger(__name__)

# Global queue for async processing
async_consumer_queue = culsans.Queue(maxsize=50)

def run_async_consumer(coroutine: Callable):
    """Wrapper function to run async_consumer with asyncio.run()"""
    asyncio.run(async_consumer(coroutine))

async def async_consumer(coroutine: Callable):
    logger = logging.getLogger(__name__)
    
    while True:
        item = await async_consumer_queue.async_q.get()
        if item is None:
            async_consumer_queue.async_q.task_done()
            logger.warning("Received shutdown signal, stopping consumer")
            break
        
        try:
            _ = asyncio.create_task(coroutine(item))
        except Exception as e:
            logger.error(f"Error processing {item=}: {type(e).__name__}: {e}", exc_info=True)
        finally:
            async_consumer_queue.async_q.task_done()

def run_async_consumer_with_task_group(coroutine: Callable, result_processor: Callable, timeout_seconds: float = 30.0, max_concurrent: int = 10):
    asyncio.run(async_consumer_with_task_group_and_result_processor(coroutine, result_processor, timeout_seconds, max_concurrent))


async def async_consumer_with_task_group_and_result_processor(coroutine: Callable, result_processor: Callable, timeout_seconds: float = 30.0, max_concurrent: int = 10):
    """
    Executes coroutines from queue with automatic timeout and concurrency limit.
    At the end of the coroutines, call the result_processor with all results
    
    Args:
        coroutine: The coroutine to execute for each queue item
        result_processor: Function that receives a list of all results from completed tasks
        timeout_seconds: Timeout in seconds for queue operations (default 30s)
        max_concurrent: Maximum number of concurrent coroutines (default 10)
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_coroutine(item):
        """Wrapper that uses semaphore to limit concurrency. Call the coroutine with None if the semaphore is not acquired."""
        locked = False
        try:
            locked = await asyncio.wait_for(semaphore.acquire(), timeout=0.001)
            return await coroutine(item)
        except asyncio.TimeoutError:
            logger.warning(f"Declining request - max concurrent limit ({max_concurrent}) reached")
            return await coroutine(None)
        finally:
            if locked:
                semaphore.release()
    
    async with asyncio.TaskGroup() as tg:
        results = []
        while True:
            try:
                # Wait for item with timeout - exits if no items received
                item = await asyncio.wait_for(
                    async_consumer_queue.async_q.get(), 
                    timeout=timeout_seconds
                )
                logger.info(f"Received item {item is None=}")
                if item is None:
                    logger.warning("Received shutdown signal, stopping consumer")
                    async_consumer_queue.async_q.task_done()
                    break
                try:
                    logger.info("Starting asyncio task")
                    task = tg.create_task(limited_coroutine(item))
                    results.append(task)
                except Exception as e:
                    logger.error(f"Error processing {item=}: {type(e).__name__}: {e}", exc_info=True)
                finally:
                    async_consumer_queue.async_q.task_done()
            except asyncio.TimeoutError:
                logger.info(f"Consumer timeout after {timeout_seconds=}s of inactivity, shutting down")
                break
                
    all_results = [result.result() for result in results]
    logger.info(f"Processing {len(all_results)} results")
    await result_processor(all_results)
