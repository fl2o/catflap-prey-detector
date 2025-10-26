import asyncio
import logging
import pytest
from catflap_prey_detector.hardware.catflap_controller import catflap_controller, handle_prey_detection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@pytest.mark.asyncio
async def test_catflap_controller():
    """Test the catflap controller functionality."""
    
    print("=== Catflap Controller Test ===\n")
    
    # Test 1: Check initial state
    print("1. Initial state:")
    status = catflap_controller.get_lock_status()
    print(f"   Locked: {status['is_locked']}")
    print(f"   Remaining time: {status['remaining_seconds']:.1f} seconds\n")
    
    # Test 2: Simulate prey detection
    print("2. Simulating prey detection...")
    message = "🔒 TEST PREY DETECTED! 🔒"
    lock_status = await handle_prey_detection()
    enhanced_message = f"{message}\n{lock_status}"
    print(f"   Original message: {message}")
    print(f"   Lock status: {lock_status}")
    print(f"   Enhanced message: {enhanced_message}\n")
    
    # Test 3: Check locked state
    print("3. After locking:")
    status = catflap_controller.get_lock_status()
    print(f"   Locked: {status['is_locked']}")
    print(f"   Remaining time: {status['remaining_seconds']:.1f} seconds")
    print(f"   Lock start: {status['lock_start_time']}\n")
    
    # Test 4: Try to lock again (should be ignored)
    print("4. Trying to lock again (should be ignored)...")
    was_locked = await catflap_controller.lock_catflap("Second attempt")
    print(f"   Lock successful: {was_locked}")
    print(f"   Remaining time: {catflap_controller.get_remaining_lock_time():.1f} seconds\n")
    
    # Test 5: Wait a bit and check remaining time
    print("5. Waiting 3 seconds...")
    await asyncio.sleep(3)
    print(f"   Remaining time: {catflap_controller.get_remaining_lock_time():.1f} seconds\n")
    
    # Test 6: Manual unlock
    print("6. Manual unlock test...")
    was_unlocked = await catflap_controller.unlock_catflap("Manual test unlock")
    print(f"   Unlock successful: {was_unlocked}")
    
    # Test 7: Final state
    print("\n7. Final state:")
    status = catflap_controller.get_lock_status()
    print(f"   Locked: {status['is_locked']}")
    print(f"   Remaining time: {status['remaining_seconds']:.1f} seconds")
    
    await asyncio.sleep(2)
    print("\n=== Test Complete ===")

@pytest.mark.asyncio
async def test_short_lock():
    """Test with a shorter lock duration for demonstration."""
    
    print("\n=== Short Lock Test (10 seconds) ===")
    
    # Temporarily set a shorter lock duration
    original_duration = catflap_controller.lock_duration_seconds
    catflap_controller.lock_duration_seconds = 10 / 60  # 10 seconds
    
    # Lock the catflap
    await catflap_controller.lock_catflap("Short test lock")
    
    # Monitor the countdown
    for i in range(12):
        remaining = catflap_controller.get_remaining_lock_time()
        is_locked = catflap_controller.is_locked
        print(f"   Second {i}: Locked={is_locked}, Remaining={remaining*60:.1f} seconds")
        await asyncio.sleep(1)
        
        if not is_locked:
            print("   Catflap automatically unlocked!")
            break
    
    # Restore original duration
    catflap_controller.lock_duration_seconds = original_duration
    print(f"   Lock duration restored to {original_duration} seconds")

if __name__ == "__main__":
    asyncio.run(test_catflap_controller())
    
    asyncio.run(test_short_lock())