import asyncio
import logging
from datetime import datetime, timedelta
from .rfid_jammer import block_catflap, unblock_catflap
from catflap_prey_detector.detection.config import catflap_config

logger = logging.getLogger(__name__)


class CatflapController:
    """Manages catflap locking with async timing and state tracking."""
    
    def __init__(self):
        self.lock_duration_seconds = catflap_config.lock_time
        self.is_locked = False
        self.lock_start_time: datetime | None = None
        self.unlock_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()  # Prevent concurrent lock/unlock operations
        
    async def lock_catflap(self, reason: str = "Prey detected") -> bool:
        """
        Lock the catflap for the specified duration.
        
        Args:
            reason: Reason for locking (for logging)
            
        Returns:
            True if lock was activated, False if already locked
        """
        async with self._lock:
            if self.is_locked:
                remaining_time = self.get_remaining_lock_time()
                logger.info(f"Catflap already locked. {remaining_time:.1f} seconds remaining")
                return False
                
            # Lock the catflap
            try:
                self._perform_lock_operation(reason)
                return True
                
            except Exception as e:
                logger.error(f"Failed to lock catflap: {e}")
                self._reset_lock_state()
                raise
                
    async def unlock_catflap(self, reason: str = "Timer expired") -> bool:
        """
        Unlock the catflap.
        
        Args:
            reason: Reason for unlocking (for logging)
            
        Returns:
            True if unlock was successful, False if not locked
        """
        async with self._lock:
            if not self.is_locked:
                logger.info("Catflap was not locked")
                return False
                
            try:
                self._perform_unlock_operation(reason)
                return True
                
            except Exception as e:
                logger.error(f"Failed to unlock catflap: {e}")
                raise
                
    async def _auto_unlock(self):
        """Internal method to automatically unlock after the timer expires."""
        logger.info("Auto-unlock timer started")
        try:
            await asyncio.sleep(self.lock_duration_seconds)
            logger.info("Auto-unlock timer finished, attempting to unlock")
            await self.unlock_catflap("Automatic timer")
        except asyncio.CancelledError:
            logger.info("Auto-unlock timer cancelled")
        finally:
            logger.info("Auto-unlock task finished")
            
    def _perform_lock_operation(self, reason: str) -> None:
        """Perform the actual lock operation with state management."""
        block_catflap()
        self.is_locked = True
        self.lock_start_time = datetime.now()
        
        # Cancel any existing unlock task
        if self.unlock_task and not self.unlock_task.done():
            self.unlock_task.cancel()
        
        self.unlock_task = asyncio.create_task(self._auto_unlock())
            
        lock_until = self.lock_start_time + timedelta(seconds=self.lock_duration_seconds)
        logger.info(f"🔒 Catflap LOCKED: {reason=}")
        logger.info(f"🕐 Lock duration: {self.lock_duration_seconds=} seconds (until {lock_until.strftime('%H:%M:%S')})")
    
    def _perform_unlock_operation(self, reason: str) -> None:
        """Perform the actual unlock operation with state management."""
        unblock_catflap()
        
        # Cancel unlock task if it exists
        if self.unlock_task and not self.unlock_task.done():
            self.unlock_task.cancel()
            
        lock_duration = (datetime.now() - self.lock_start_time).total_seconds()
        logger.info(f"🔓 Catflap UNLOCKED: {reason=}")
        logger.info(f"🕐 Was locked for {lock_duration:.1f} seconds")
        
        self.is_locked = False
        self.lock_start_time = None
        self.unlock_task = None
    
    def _reset_lock_state(self) -> None:
        """Reset lock state after a failed operation."""
        self.is_locked = False
        self.lock_start_time = None
            
    def get_remaining_lock_time(self) -> float:
        """Get remaining lock time in minutes. Returns 0 if not locked."""
        if not self.is_locked or not self.lock_start_time:
            return 0.0
            
        elapsed = (datetime.now() - self.lock_start_time).total_seconds()
        remaining = max(0, self.lock_duration_seconds - elapsed)
        return remaining
        
    def get_lock_status(self) -> dict:
        """Get detailed lock status information."""
        return {
            "is_locked": self.is_locked,
            "lock_start_time": self.lock_start_time.isoformat() if self.lock_start_time else None,
            "remaining_seconds": self.get_remaining_lock_time(),
            "lock_duration_seconds": self.lock_duration_seconds
        }


catflap_controller = CatflapController()


async def handle_prey_detection() -> str:
    """
    Handle prey detection by locking the catflap and returning the lock status message.
    
    Returns:
        Lock status message for joining with detection message
    """
    try:
        logger.info("Locking catflap")
        await catflap_controller.lock_catflap("Cat with prey detected")
        remaining = catflap_controller.get_remaining_lock_time()
        return f"🕐 Catflap locked for {remaining:.1f} more seconds"
        
    except Exception as e:
        logger.error(f"Error handling prey detection: {e}")
        return "⚠️ Warning: Could not lock catflap"


class DetectionPauser:
    """Optional helper to pause detection during catflap lock."""
    
    def __init__(self, controller: CatflapController):
        self.controller = controller
        
    def should_pause_detection(self) -> bool:
        """Returns True if detection should be paused due to catflap lock."""
        return self.controller.is_locked
        
    def get_pause_reason(self) -> str:
        """Get reason for detection pause."""
        if self.controller.is_locked:
            remaining = self.controller.get_remaining_lock_time()
            return f"Detection paused - catflap locked for {remaining:.1f} more seconds"
        return ""


detection_pauser = DetectionPauser(catflap_controller)
