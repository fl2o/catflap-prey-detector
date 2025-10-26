import os
import logging
import asyncio
from io import BytesIO

from telegram import Update, ReactionTypeEmoji
from telegram.constants import ReactionEmoji
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from telegram.error import TimedOut, NetworkError, TelegramError
import httpcore
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    retry_if_exception_type,
    before_sleep_log,
)

from catflap_prey_detector.hardware.catflap_controller import catflap_controller
from catflap_prey_detector.detection.camera_manager import CameraManager

logger = logging.getLogger(__name__)

# Global camera manager instance
camera_manager: CameraManager | None = None

BOT_TOKEN = os.getenv("BOT_TOKEN")

GROUP_ID = int(os.getenv("GROUP_ID"))

def notify_event(text: str, image_bytes: bytes | None = None) -> None:
    """Send notification from sync context (e.g., detection thread).
    
    Args:
        text: The notification text to send
        image_bytes: Optional image data in bytes format (e.g., JPEG)
    """
    try:
        # Import here to avoid circular dependency
        from catflap_prey_detector.main import MAIN_LOOP
        if MAIN_LOOP is None:
            logger.error("Cannot send notification: MAIN_LOOP not initialized")
            return
            
        asyncio.run_coroutine_threadsafe(
            notify_event_async(text, image_bytes),
            MAIN_LOOP
        )
        logger.debug(f"Scheduled notification from sync context: {text=} (with_image={image_bytes is not None})")
    except Exception as e:
        logger.error(f"Failed to send notification from sync context: {e}", exc_info=True)


async def notify_event_async(text: str, image_bytes: bytes | None = None) -> None:
    """Send notification from async context.
    
    Args:
        text: The notification text to send
        image_bytes: Optional image data in bytes format (e.g., JPEG)
    """
    try:
        await _send_telegram_message(text, image_bytes)
        logger.debug(f"Sent notification from async context: {text=} (with_image={image_bytes is not None})")
    except Exception as e:
        logger.error(f"Failed to send notification from async context: {e}", exc_info=True)

@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((TimedOut, NetworkError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _send_telegram_message(
    text: str, 
    image_bytes: bytes | None = None
) -> None:
    """Send a message to Telegram with retry logic using tenacity.
    
    Args:
        context: Telegram bot context
        text: The message text to send
        image_bytes: Optional image data in bytes format (e.g., JPEG)
    
    Raises:
        TelegramError: For non-retryable Telegram errors
        TimedOut, NetworkError: For network-related errors (after retries exhausted)
    """
    logger.info(f"Sending message to Telegram: {text=} (with_image={image_bytes is not None})")
    
    try:
        if image_bytes:
            image_io = BytesIO(image_bytes)
            image_io.name = "detection.jpg"
            logger.debug(f"Sending photo with caption, image size: {len(image_bytes)=} bytes")
            await app.bot.send_photo(
                chat_id=GROUP_ID, 
                photo=image_io, 
                caption=text
            )
        else:
            logger.debug("Sending text-only message")
            await app.bot.send_message(chat_id=GROUP_ID, text=text)
            
        logger.info("Message sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise

@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((TimedOut, NetworkError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"Ping command received from user {update.effective_user.id=}")
    await update.message.reply_text("pong")

# Convenience: find the current chat/topic IDs (send /where in the group)
async def cmd_where(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cid = update.effective_chat.id
    tid = getattr(update.effective_message, "message_thread_id", None)
    logger.info(f"Where command received from user {update.effective_user.id=}, {cid=}, {tid=}")
    await update.message.reply_text(f"chat_id={cid}\nthread_id={tid}")


@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((TimedOut, NetworkError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def cmd_lock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lock the catflap manually via Telegram command."""
    user_id = update.effective_user.id
    logger.info(f"Lock command received from user {user_id=}")

    success = await catflap_controller.lock_catflap("Manual lock via Telegram")

    if success:
        remaining = catflap_controller.get_remaining_lock_time()
        response = f"🔒 Catflap locked successfully!\n🕐 Lock duration: {remaining:.1f} seconds"
    else:
        remaining = catflap_controller.get_remaining_lock_time()
        response = f"ℹ️ Catflap is already locked.\n🕐 Remaining time: {remaining:.1f} seconds"

    await update.message.reply_text(response)


@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((TimedOut, NetworkError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def cmd_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unlock the catflap manually via Telegram command."""
    user_id = update.effective_user.id
    logger.info(f"Unlock command received from user {user_id=}")

    success = await catflap_controller.unlock_catflap("Manual unlock via Telegram")

    if success:
        response = "🔓 Catflap unlocked successfully!"
    else:
        response = "ℹ️ Catflap was not locked."

    await update.message.reply_text(response)


@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((TimedOut, NetworkError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get the current status of the catflap via Telegram command."""
    user_id = update.effective_user.id
    logger.info(f"Status command received from user {user_id=}")

    status = catflap_controller.get_lock_status()

    if status["is_locked"]:
        remaining = status["remaining_seconds"]
        lock_time = status["lock_start_time"]
        response = (
            f"🔒 Catflap Status: LOCKED\n"
            f"🕐 Remaining time: {remaining:.1f} seconds\n"
            f"📅 Locked since: {lock_time}"
        )
    else:
        response = "🔓 Catflap Status: UNLOCKED"

    await update.message.reply_text(response)


@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((TimedOut, NetworkError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def cmd_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Capture and send a photo from the camera."""
    user_id = update.effective_user.id
    logger.info(f"Photo command received from user {user_id=}")

    await update.message.set_reaction(ReactionTypeEmoji(ReactionEmoji.EYES))

    global camera_manager

    if camera_manager is None or not camera_manager._started:
        await update.message.reply_text("❌ Camera is not available. The detection system may not be running.")
        return

    image_bytes = camera_manager.capture_image_bytes(quality=90)

    if image_bytes:
        image_io = BytesIO(image_bytes)
        image_io.name = "capture.jpg"

        await update.message.reply_photo(
            photo=image_io,
            caption="📸 Live camera capture"
        )
        logger.info("Photo sent successfully")
    else:
        await update.message.reply_text("❌ Failed to capture image from camera")
        logger.error("Failed to capture image - no bytes returned")


async def send_startup_message() -> None:
    """Send a funny French startup message when the bot starts"""
    startup_text = "🐱 Bonjour les humains! Le proie-tecteur est maintenant opérationnel 🐭"
    
    try:
        await _send_telegram_message(startup_text)
        logger.info("Sent startup message to group")
    except (TimedOut, NetworkError) as e:
        logger.warning(f"Failed to send startup message due to network error: {e}")
    except TelegramError as e:
        logger.error(f"Failed to send startup message: {e}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by Updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    if isinstance(context.error, (httpcore.ReadError, httpx.ReadError)):
        logger.warning("HTTP read error - this is usually temporary and caused by network instability")
    elif isinstance(context.error, TimedOut):
        logger.warning("Timeout error - this is usually temporary")
    elif isinstance(context.error, NetworkError):
        logger.warning("Network error - check internet connection")
    elif isinstance(context.error, TelegramError):
        logger.error(f"Telegram API error: {context.error=}")


def polling_error_callback(error: Exception) -> None:
    """Handle errors during polling (non-async version for start_polling)."""
    
    if isinstance(error, (httpcore.ReadError, httpx.ReadError)):
        logger.warning("HTTP read error during polling - this is usually temporary and caused by network instability")
    elif isinstance(error, TimedOut):
        logger.warning("Timeout error during polling - this is usually temporary")
    elif isinstance(error, NetworkError):
        logger.warning("Network error during polling - check internet connection")
    elif isinstance(error, TelegramError):
        logger.error(f"Telegram API error during polling: {error=}")
    else:
        logger.error("Error during polling:", exc_info=error)


app = Application.builder().token(BOT_TOKEN).build()

async def main() -> None:
    logger.info("Initializing Telegram bot...")
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set")
        raise ValueError("BOT_TOKEN environment variable is required")
    
    if not GROUP_ID:
        logger.error("GROUP_ID environment variable is not set")
        raise ValueError("GROUP_ID environment variable is required")
    
    logger.info(f"Bot configured for {GROUP_ID=}")
    
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("where", cmd_where))
    app.add_handler(CommandHandler("lock", cmd_lock))
    app.add_handler(CommandHandler("unlock", cmd_unlock))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("photo", cmd_photo))
    app.add_error_handler(error_handler)
    logger.info("Command handlers registered")
    
    await app.initialize()
    logger.info("Bot application initialized")
    
    await app.start()
    logger.info("Bot started successfully")
    
    await send_startup_message()
    
    # Start polling in the background
    await app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        error_callback=polling_error_callback
    )
    logger.info("Bot polling started, waiting for messages...")
    
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        logger.info("Bot polling cancelled, shutting down...")
        await app.updater.stop()
        await app.stop()


async def test_notification() -> None:
    """Test function to send a notification after bot startup"""
    import asyncio
    
    await asyncio.sleep(5)
    logger.info('Sending test notification from async context')
    await notify_event_async("🧪 Test notification from async context!", None)
    
    import threading
    def test_sync_notification():
        logger.info('Sending test notification from sync context')
        notify_event("🧪 Test notification from sync context (thread)!", None)
    
    thread = threading.Thread(target=test_sync_notification)
    thread.start()
    thread.join()
    
    await asyncio.sleep(5)


async def main_with_test() -> None:
    """Run the bot with a test notification"""
    import asyncio
    
    logger.info("Starting bot with test notification")
    bot_task = asyncio.create_task(main())
    
    test_task = asyncio.create_task(test_notification())
    
    await test_task
    bot_task.cancel()
    
    try:
        await bot_task
    except asyncio.CancelledError:
        logger.info("Bot stopped after test")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main_with_test())

