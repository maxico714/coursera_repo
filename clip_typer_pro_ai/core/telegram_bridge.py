"""
Telegram Bridge for ClipTyper Pro + AI Assistant
Implements bi-directional Telegram integration with auto-copy and auto-type features.
"""
import asyncio
import threading
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime
import re
from models.telegram_message import TelegramMessage
from utils.logger import get_logger


class TelegramBridge:
    """
    Bi-directional Telegram integration with auto-copy and auto-type features.
    Handles both receiving messages from Telegram and sending content to Telegram.
    """
    
    def __init__(self, settings_manager, event_dispatcher, clipboard_manager):
        self.settings_manager = settings_manager
        self.event_dispatcher = event_dispatcher
        self.clipboard_manager = clipboard_manager
        self.logger = get_logger('telegram_bridge')
        
        # Telegram configuration
        self.bot_token = settings_manager.get('telegram.bot_token', '')
        self.user_ids = settings_manager.get('telegram.user_ids', [])
        self.enabled = settings_manager.get('telegram.enabled', False)
        self.auto_copy_from_telegram = settings_manager.get('telegram.auto_copy_from_telegram', False)
        self.auto_type_responses = settings_manager.get('telegram.auto_type_responses', False)
        self.connection_method = settings_manager.get('telegram.connection_method', 'polling')  # 'webhook' or 'polling'
        
        # Bridge state
        self.running = False
        self.bridge_thread = None
        self.updater = None
        self.application = None
        
        # Message history
        self.message_history = []
        self.max_history = 100
        
        # Rate limiting
        self.last_message_time = {}
        self.min_message_interval = 1.0  # Minimum seconds between messages
        
        self.logger.info(f"Telegram bridge initialized (enabled: {self.enabled})")
    
    def start(self):
        """Start the Telegram bridge."""
        if self.running or not self.enabled or not self.bot_token:
            self.logger.warning("Cannot start Telegram bridge - not enabled or missing token")
            return False
        
        try:
            # Import telegram libraries inside the method to handle optional dependencies
            from telegram.ext import Application, CommandHandler, MessageHandler, filters
            
            # Create the application
            self.application = Application.builder().token(self.bot_token).build()
            
            # Add handlers
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_telegram_message))
            self.application.add_handler(CommandHandler("start", self._handle_start_command))
            self.application.add_handler(CommandHandler("help", self._handle_help_command))
            self.application.add_handler(CommandHandler("status", self._handle_status_command))
            
            # Start the bot
            self.running = True
            
            if self.connection_method == 'polling':
                # Run polling in a separate thread
                self.bridge_thread = threading.Thread(target=self._run_polling, daemon=True)
                self.bridge_thread.start()
                self.logger.info("Telegram bridge started with polling")
            else:
                self.logger.warning("Webhook mode not fully implemented yet, using polling instead")
                self.bridge_thread = threading.Thread(target=self._run_polling, daemon=True)
                self.bridge_thread.start()
            
            self.event_dispatcher.dispatch('telegram_bridge_started', {})
            return True
            
        except ImportError:
            self.logger.error("python-telegram-bot not installed. Install with: pip install python-telegram-bot")
            return False
        except Exception as e:
            self.logger.error(f"Error starting Telegram bridge: {str(e)}", exc_info=True)
            return False
    
    def stop(self):
        """Stop the Telegram bridge."""
        if not self.running:
            return
        
        try:
            self.running = False
            
            if self.application:
                # Stop the application gracefully
                try:
                    # For newer versions of python-telegram-bot, use async shutdown
                    asyncio.run(self._shutdown_application())
                except:
                    # Fallback for older versions
                    pass
            
            if self.bridge_thread:
                self.bridge_thread.join(timeout=5.0)  # Wait up to 5 seconds
            
            self.logger.info("Telegram bridge stopped")
            self.event_dispatcher.dispatch('telegram_bridge_stopped', {})
            
        except Exception as e:
            self.logger.error(f"Error stopping Telegram bridge: {str(e)}", exc_info=True)
    
    async def _shutdown_application(self):
        """Shutdown the telegram application."""
        if self.application:
            await self.application.shutdown()
    
    def _run_polling(self):
        """Run the telegram bot in polling mode."""
        try:
            # Run the application
            self.application.run_polling(stop_signals=None)  # Disable default stop signals
        except Exception as e:
            if self.running:  # Only log error if we didn't intentionally stop
                self.logger.error(f"Error in Telegram polling: {str(e)}", exc_info=True)
    
    async def _handle_telegram_message(self, update, context):
        """Handle incoming messages from Telegram."""
        try:
            # Check if sender is authorized
            user_id = str(update.effective_user.id)
            if self.user_ids and user_id not in self.user_ids:
                self.logger.info(f"Unauthorized user {user_id} tried to send message")
                await update.message.reply_text("You are not authorized to use this bot.")
                return
            
            # Get message text
            message_text = update.message.text
            
            # Create telegram message object
            tg_message = TelegramMessage(
                message_id=update.message.message_id,
                user_id=user_id,
                username=update.effective_user.username,
                text=message_text,
                timestamp=datetime.fromtimestamp(update.message.date.timestamp())
            )
            
            # Add to history
            self._add_to_message_history(tg_message)
            
            self.logger.info(f"Received message from Telegram user {user_id}: {message_text[:50]}...")
            
            # Auto-copy to clipboard if enabled
            if self.auto_copy_from_telegram:
                import pyperclip
                pyperclip.copy(message_text)
                self.logger.info("Auto-copied message to clipboard")
                
                # Optionally auto-type if enabled
                if self.auto_type_responses:
                    from core.typing_engine import TypingEngine  # Import here to avoid circular dependency
                    # We'd need to get the typing engine from the main app, so we'll dispatch an event instead
                    self.event_dispatcher.dispatch('auto_type_request', {
                        'text': message_text,
                        'source': 'telegram'
                    })
            
            # Process with AI if requested (if message starts with certain prefix)
            if message_text.lower().startswith('/ai ') or message_text.lower().startswith('/ask '):
                ai_query = re.sub(r'^/ai\s+|^/ask\s+', '', message_text, flags=re.IGNORECASE)
                await self._process_with_ai(update, context, ai_query)
            
            # Acknowledge receipt
            await update.message.reply_text("✓ Message received and processed")
            
            # Dispatch event
            self.event_dispatcher.dispatch('telegram_message_received', {
                'user_id': user_id,
                'message_length': len(message_text),
                'auto_copy_enabled': self.auto_copy_from_telegram,
                'auto_type_enabled': self.auto_type_responses
            })
            
        except Exception as e:
            self.logger.error(f"Error handling Telegram message: {str(e)}", exc_info=True)
            try:
                await update.message.reply_text("Sorry, an error occurred while processing your message.")
            except:
                pass  # Ignore errors when trying to send error message
    
    async def _process_with_ai(self, update, context, query: str):
        """Process a query with AI and send response back to Telegram."""
        try:
            # Dispatch event to main AI processor (would be handled by main app)
            self.event_dispatcher.dispatch('ai_request_from_telegram', {
                'query': query,
                'user_id': str(update.effective_user.id),
                'message_id': update.message.message_id
            })
            
            # For now, send a placeholder response
            await update.message.reply_text("AI processing requested. The response will be handled by the main application.")
            
        except Exception as e:
            self.logger.error(f"Error processing AI request from Telegram: {str(e)}", exc_info=True)
            await update.message.reply_text("Sorry, an error occurred while processing your AI request.")
    
    async def _handle_start_command(self, update, context):
        """Handle /start command."""
        welcome_msg = (
            "👋 Welcome to ClipTyper Pro + AI Assistant Telegram Bridge!\n\n"
            "Available commands:\n"
            "/start - Show this message\n"
            "/help - Show help information\n"
            "/status - Show bridge status\n"
            "/ai [query] - Process query with AI\n\n"
            "Messages sent here can be automatically copied to your computer clipboard."
        )
        await update.message.reply_text(welcome_msg)
    
    async def _handle_help_command(self, update, context):
        """Handle /help command."""
        help_msg = (
            "📚 Help - ClipTyper Pro + AI Assistant\n\n"
            "This bot bridges your Telegram messages to your computer:\n\n"
            "• Send any text message to have it appear on your computer\n"
            "• Use /ai followed by your query to process with AI\n"
            "• Configure auto-copy and auto-type in the app settings\n\n"
            "For more information, check the desktop application."
        )
        await update.message.reply_text(help_msg)
    
    async def _handle_status_command(self, update, context):
        """Handle /status command."""
        status_msg = (
            f"📊 Bridge Status:\n\n"
            f"Enabled: {'Yes' if self.enabled else 'No'}\n"
            f"Auto-copy: {'Yes' if self.auto_copy_from_telegram else 'No'}\n"
            f"Auto-type: {'Yes' if self.auto_type_responses else 'No'}\n"
            f"Connection: {self.connection_method}\n"
            f"Authorized users: {len(self.user_ids)}\n"
            f"Messages processed: {len(self.message_history)}"
        )
        await update.message.reply_text(status_msg)
    
    def send_to_telegram(self, text: str, user_id: Optional[str] = None) -> bool:
        """
        Send text to Telegram chat.
        
        Args:
            text: Text to send
            user_id: Specific user ID to send to (if None, sends to all authorized users)
            
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled or not self.bot_token:
            self.logger.warning("Cannot send to Telegram - bridge not enabled or no token")
            return False
        
        # Rate limiting
        current_time = time.time()
        if user_id in self.last_message_time:
            time_since_last = current_time - self.last_message_time[user_id]
            if time_since_last < self.min_message_interval:
                self.logger.warning(f"Rate limited - waiting {self.min_message_interval - time_since_last:.1f}s")
                time.sleep(self.min_message_interval - time_since_last)
        
        try:
            # Import here to handle optional dependency
            from telegram import Bot
            
            bot = Bot(token=self.bot_token)
            
            # Determine recipients
            recipients = [user_id] if user_id else self.user_ids
            
            if not recipients:
                self.logger.warning("No recipients specified and no authorized users configured")
                return False
            
            success_count = 0
            for recipient_id in recipients:
                try:
                    asyncio.run(self._send_message_to_user(bot, recipient_id, text))
                    success_count += 1
                    time.sleep(0.1)  # Small delay between messages
                except Exception as e:
                    self.logger.error(f"Failed to send message to user {recipient_id}: {str(e)}")
            
            self.last_message_time[user_id or 'default'] = current_time
            
            self.logger.info(f"Sent message to {success_count}/{len(recipients)} users")
            self.event_dispatcher.dispatch('telegram_message_sent', {
                'recipients_count': len(recipients),
                'successful_sends': success_count,
                'content_length': len(text)
            })
            
            return success_count > 0
            
        except ImportError:
            self.logger.error("python-telegram-bot not installed")
            return False
        except Exception as e:
            self.logger.error(f"Error sending message to Telegram: {str(e)}", exc_info=True)
            return False
    
    async def _send_message_to_user(self, bot, user_id: str, text: str):
        """Send a message to a specific user."""
        # Split long messages into chunks if needed
        max_length = 4096  # Telegram's max message length
        
        if len(text) <= max_length:
            await bot.send_message(chat_id=int(user_id), text=text)
        else:
            # Split into chunks
            chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
            for i, chunk in enumerate(chunks):
                if i == len(chunks) - 1:
                    # Add indicator for last message if it was split
                    await bot.send_message(chat_id=int(user_id), text=f"{chunk}\n\n[Part {i+1}/{len(chunks)} - Final]")
                else:
                    await bot.send_message(chat_id=int(user_id), text=f"{chunk}\n\n[Part {i+1}/{len(chunks)} - Continued...]")
                await asyncio.sleep(0.5)  # Delay between chunks
    
    def _add_to_message_history(self, message: TelegramMessage):
        """Add a message to the history."""
        self.message_history.insert(0, message)
        
        # Trim history if too large
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[:self.max_history]
    
    def get_message_history(self, limit: Optional[int] = None) -> List[TelegramMessage]:
        """Get message history."""
        if limit is None:
            return self.message_history.copy()
        else:
            return self.message_history[:limit]
    
    def clear_message_history(self):
        """Clear message history."""
        old_count = len(self.message_history)
        self.message_history.clear()
        self.logger.info(f"Cleared message history ({old_count} messages removed)")
    
    def set_bot_token(self, token: str):
        """Set the Telegram bot token."""
        self.bot_token = token
        self.settings_manager.set('telegram.bot_token', token)
        self.logger.info("Telegram bot token updated")
    
    def set_user_ids(self, user_ids: List[str]):
        """Set authorized user IDs."""
        self.user_ids = [str(uid) for uid in user_ids]
        self.settings_manager.set('telegram.user_ids', self.user_ids)
        self.logger.info(f"Updated authorized user IDs: {self.user_ids}")
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the Telegram bridge."""
        self.enabled = enabled
        self.settings_manager.set('telegram.enabled', enabled)
        
        if enabled and not self.running:
            self.start()
        elif not enabled and self.running:
            self.stop()
        
        self.logger.info(f"Telegram bridge {'enabled' if enabled else 'disabled'}")
    
    def set_auto_copy_from_telegram(self, enabled: bool):
        """Enable or disable auto-copy from Telegram."""
        self.auto_copy_from_telegram = enabled
        self.settings_manager.set('telegram.auto_copy_from_telegram', enabled)
        self.logger.info(f"Auto-copy from Telegram {'enabled' if enabled else 'disabled'}")
    
    def set_auto_type_responses(self, enabled: bool):
        """Enable or disable auto-typing of responses."""
        self.auto_type_responses = enabled
        self.settings_manager.set('telegram.auto_type_responses', enabled)
        self.logger.info(f"Auto-type responses {'enabled' if enabled else 'disabled'}")
    
    def set_connection_method(self, method: str):
        """Set the connection method (polling or webhook)."""
        if method in ['polling', 'webhook']:
            self.connection_method = method
            self.settings_manager.set('telegram.connection_method', method)
            self.logger.info(f"Connection method set to {method}")
            
            # Restart if currently running
            if self.running:
                self.stop()
                self.start()
        else:
            self.logger.warning(f"Invalid connection method: {method}. Use 'polling' or 'webhook'")
    
    def test_connection(self) -> bool:
        """Test the Telegram bot connection."""
        try:
            from telegram import Bot
            import asyncio
            
            bot = Bot(token=self.bot_token)
            # Get bot info to test connection
            bot_info = asyncio.run(bot.get_me())
            self.logger.info(f"Successfully connected to Telegram bot: @{bot_info.username}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Telegram: {str(e)}")
            return False
    
    def get_status(self) -> Dict:
        """Get the current status of the Telegram bridge."""
        return {
            'enabled': self.enabled,
            'running': self.running,
            'has_token': bool(self.bot_token),
            'authorized_users_count': len(self.user_ids),
            'auto_copy_enabled': self.auto_copy_from_telegram,
            'auto_type_enabled': self.auto_type_responses,
            'connection_method': self.connection_method,
            'message_history_count': len(self.message_history)
        }
    
    def send_clipboard_content_to_telegram(self, user_id: Optional[str] = None) -> bool:
        """Send current clipboard content to Telegram."""
        try:
            import pyperclip
            clipboard_content = pyperclip.paste()
            
            if clipboard_content:
                return self.send_to_telegram(clipboard_content, user_id)
            else:
                self.logger.warning("Clipboard is empty, nothing to send")
                return False
        except ImportError:
            self.logger.error("pyperclip not available")
            return False
        except Exception as e:
            self.logger.error(f"Error sending clipboard content to Telegram: {str(e)}")
            return False