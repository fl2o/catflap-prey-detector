import pytest
from unittest.mock import AsyncMock, MagicMock
from conftest import skip_if_no_telegram


@pytest.mark.asyncio
async def test_cmd_status_mock():
    from catflap_prey_detector.notifications.telegram_bot import cmd_status
    from catflap_prey_detector.hardware.catflap_controller import catflap_controller
    
    update = MagicMock()
    update.effective_user.id = 12345
    update.message.reply_text = AsyncMock()
    
    context = MagicMock()
    
    await cmd_status(update, context)
    
    expected_call_count = 1
    assert update.message.reply_text.call_count == expected_call_count


@skip_if_no_telegram
@pytest.mark.asyncio
async def test_cmd_ping_real():
    from catflap_prey_detector.notifications.telegram_bot import cmd_ping
    
    update = MagicMock()
    update.effective_user.id = 12345
    update.message.reply_text = AsyncMock()
    
    context = MagicMock()
    
    await cmd_ping(update, context)
    
    expected_text = "pong"
    update.message.reply_text.assert_called_once_with(expected_text)

