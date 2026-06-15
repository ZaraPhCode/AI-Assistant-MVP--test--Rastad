import logging
import requests
import os
from functools import wraps
import time
from typing import Optional

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Retry decorator
# ------------------------------------------------------------------
def retry(max_attempts=3, delay=1, backoff=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            last_exception = None
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    last_exception = e
                    if attempts < max_attempts:
                        logger.warning(f"Attempt {attempts} failed, retrying in {current_delay}s: {str(e)}")
                        time.sleep(current_delay)
                        current_delay *= backoff
                        continue
                    logger.error(f"All {max_attempts} attempts failed")
                    raise last_exception
        return wrapper
    return decorator


class TelegramBot:
    def __init__(self):
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.warning("TELEGRAM_BOT_TOKEN not set! Telegram bot will not work.")
            self.base_url = None
        else:
            self.base_url = f"https://api.telegram.org/bot{token}"
        
        # Store user states in memory (temporary - for MVP)
        # Format: {chat_id: {"state": "awaiting_name"|"awaiting_id"|"awaiting_message"|"menu", 
        #                      "temp_name": "...", "temp_user_id": "..."}}
        self.user_states = {}
    
    @retry(max_attempts=3, delay=1, backoff=2)
    def send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown",
                     reply_markup: Optional[dict] = None) -> bool:
        """Send a message to a Telegram chat"""
        if not self.base_url:
            logger.error("Telegram bot not configured")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 429:
                retry_after = response.json().get('parameters', {}).get('retry_after', 5)
                logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                time.sleep(retry_after)
                raise requests.exceptions.RequestException(f"Rate limited")
                
            response.raise_for_status()
            logger.info(f"Message sent to chat_id {chat_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            raise
    
    def show_main_menu(self, chat_id: int):
        """Show the main menu with inline keyboard"""
        keyboard = {
            "keyboard": [
                [{"text": "📝 ارسال پیام"}],
                [{"text": "ℹ️ درباره ربات"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        
        self.send_message(
            chat_id,
            "🏠 *منوی اصلی*\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=keyboard
        )
    
    def show_categories_menu(self, chat_id: int):
        """Show predefined categories"""
        keyboard = {
            "keyboard": [
                [{"text": "🌟 خدمات VIP"}],
                [{"text": "📊 ثبت‌نام در صرافی"}],
                [{"text": "🤝 همکاری KOL"}],
                [{"text": "🆘 مشکل پرداخت / پشتیبانی"}],
                [{"text": "📈 Trade Assist"}],
                [{"text": "✍️ پیام دلخواه"}],
                [{"text": "🔙 بازگشت به منوی اصلی"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        
        self.send_message(
            chat_id,
            "📋 *دسته‌بندی موضوعات*\n\n"
            "یکی از موضوعات زیر را انتخاب کنید یا پیام دلخواه خود را بنویسید:",
            reply_markup=keyboard
        )
    
    def request_user_info(self, chat_id: int):
        """Start the flow to collect user name and ID"""
        self.user_states[chat_id] = {"state": "awaiting_name", "temp_name": None, "temp_user_id": None}
        
        # Show cancel button
        keyboard = {
            "keyboard": [
                [{"text": "🔙 انصراف"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": True
        }
        
        self.send_message(
            chat_id,
            "👤 *لطفاً نام خود را وارد کنید:*\n\n"
            "مثال: علی محمدی",
            reply_markup=keyboard
        )
    
    def handle_message(self, chat_id: int, text: str):
        """Process incoming messages based on user state"""
        
        # Check if user is in a flow
        state_data = self.user_states.get(chat_id, {})
        state = state_data.get("state", None)
        
        # Handle cancel
        if text == "🔙 انصراف":
            if chat_id in self.user_states:
                del self.user_states[chat_id]
            self.show_main_menu(chat_id)
            return
        
        if text == "🔙 بازگشت به منوی اصلی":
            if chat_id in self.user_states:
                del self.user_states[chat_id]
            self.show_main_menu(chat_id)
            return
        
        # State machine
        if state == "awaiting_name":
            state_data["temp_name"] = text
            state_data["state"] = "awaiting_id"
            
            keyboard = {
                "keyboard": [[{"text": "🔙 انصراف"}]],
                "resize_keyboard": True,
                "one_time_keyboard": True
            }
            
            self.send_message(
                chat_id,
                f"✅ نام: *{text}*\n\n"
                "🔢 *حالا شناسه کاربری خود را وارد کنید:*\n\n"
                "مثال: 12345",
                reply_markup=keyboard
            )
            return
        
        if state == "awaiting_id":
            state_data["temp_user_id"] = text
            state_data["state"] = "menu"  # Ready to accept questions
            
            self.send_message(
                chat_id,
                f"✅ اطلاعات شما ثبت شد:\n"
                f"👤 نام: *{state_data['temp_name']}*\n"
                f"🆔 شناسه: *{text}*\n\n"
                f"حالا می‌توانید سوال خود را بپرسید."
            )
            
            # Show categories menu
            self.show_categories_menu(chat_id)
            return
        
        # NEW: If user is in "menu" state or "awaiting_message" state,
        # treat any non-button text as a question
        if state in ["menu", "awaiting_message"]:
            # Check if it's a menu button
            menu_buttons = [
                "📝 ارسال پیام", "ℹ️ درباره ربات", "🔙 بازگشت به منوی اصلی",
                "🌟 خدمات VIP", "📊 ثبت‌نام در صرافی", "🤝 همکاری KOL",
                "🆘 مشکل پرداخت / پشتیبانی", "📈 Trade Assist", "✍️ پیام دلخواه"
            ]
            if text in menu_buttons:
                self.process_menu_choice(chat_id, text)
            else:
                # It's a question - send to API
                self.forward_to_api(chat_id, text)
            return
        
        # Default: process as menu choice
        self.process_menu_choice(chat_id, text)
    
    def process_menu_choice(self, chat_id: int, text: str):
        """Process menu selections"""
        
        # Main menu options
        if text == "📝 ارسال پیام":
            self.request_user_info(chat_id)
            return
        
        if text == "ℹ️ درباره ربات":
            self.send_message(
                chat_id,
                "🤖 *دستیار هوشمند راستاد*\n\n"
                "این ربات برای پاسخگویی به سوالات شما درباره خدمات راستاد طراحی شده است.\n\n"
                "📌 *خدمات قابل پشتیبانی:*\n"
                "• خدمات VIP\n"
                "• ثبت‌نام در صرافی\n"
                "• همکاری KOL\n"
                "• پشتیبانی و مشکلات\n"
                "• اطلاعات عمومی\n\n"
                "💡 کافیست گزینه «ارسال پیام» را بزنید و سوال خود را بپرسید."
            )
            self.show_main_menu(chat_id)
            return
        
        # Category options - map to actual messages
        category_messages = {
            "🌟 خدمات VIP": "خدمات VIP راستاد چیست؟",
            "📊 ثبت‌نام در صرافی": "چطور در صرافی ثبت‌نام کنم؟",
            "🤝 همکاری KOL": "می‌خواهم KOL بشم",
            "🆘 مشکل پرداخت / پشتیبانی": "مشکل پرداخت دارم",
            "📈 Trade Assist": "Trade Assist چیست؟",
        }
        
        if text in category_messages:
            self.forward_to_api(chat_id, category_messages[text])
            return
        
        if text == "✍️ پیام دلخواه":
            state_data = self.user_states.get(chat_id, {})
            state_data["state"] = "awaiting_message"
            
            keyboard = {
                "keyboard": [[{"text": "🔙 بازگشت به منوی اصلی"}]],
                "resize_keyboard": True,
                "one_time_keyboard": False
            }
            
            self.send_message(
                chat_id,
                "✍️ *پیام خود را بنویسید:*\n\n"
                "هر سوالی دارید بپرسید.",
                reply_markup=keyboard
            )
            return
        
        # Check if user is in "awaiting_message" state
        state_data = self.user_states.get(chat_id, {})
        if state_data.get("state") == "awaiting_message":
            self.forward_to_api(chat_id, text)
            return
        
        # Unknown command
        self.send_message(
            chat_id,
            "⚠️ لطفاً از منوی زیر گزینه مورد نظر را انتخاب کنید."
        )
        self.show_main_menu(chat_id)
    
    def forward_to_api(self, chat_id: int, message_text: str):
        """Forward the user's message to the API and return the response"""
        state_data = self.user_states.get(chat_id, {})
        user_name = state_data.get("temp_name", "Telegram User")
        user_id = state_data.get("temp_user_id", str(chat_id))
        
        if not user_name or not user_id:
            self.send_message(
                chat_id,
                "❌ لطفاً ابتدا از منوی اصلی گزینه «ارسال پیام» را انتخاب کنید."
            )
            self.show_main_menu(chat_id)
            return
        
        # Call the internal functions directly instead of HTTP request
        try:
            from app.services.classifier import classify_message
            from app.services.knowledge_service import knowledge_service
            from app.services.llm_service import llm_service
            from app.database import SessionLocal
            from app.models import User, Message
            from datetime import datetime, timezone
            
            # 1. Classify
            intent, segment, needs_human = classify_message(message_text)
            
            # 2. Search knowledge base
            knowledge = knowledge_service.search(message_text)
            
            # 3. Generate reply
            reply = llm_service.generate_reply(intent, knowledge, message_text)
            
            # 4. Save to database
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    user = User(
                        user_id=user_id,
                        name=user_name,
                        segment=segment,
                        created_at=datetime.now(timezone.utc),
                        last_seen_at=datetime.now(timezone.utc),
                    )
                    db.add(user)
                else:
                    user.name = user_name
                    user.segment = segment
                    user.last_seen_at = datetime.now(timezone.utc)
                
                msg_record = Message(
                    user_id=user_id,
                    user_message=message_text,
                    assistant_reply=reply,
                    intent=intent,
                    needs_human_support=needs_human,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(msg_record)
                db.commit()
                
                logger.info(f"Saved to DB - user_id={user_id}, intent={intent}")
                
            except Exception as e:
                db.rollback()
                logger.error(f"Database error: {str(e)}")
            finally:
                db.close()
            
            # 5. Build response message
            reply_text = (
                f"📩 *پاسخ دستیار راستاد:*\n\n"
                f"{reply}\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🏷️ *دسته‌بندی:* {intent}\n"
                f"👤 *سگمنت:* {segment}\n"
            )
            
            if needs_human:
                reply_text += "⚠️ *نیاز به پشتیبانی انسانی:* بله\n"
                reply_text += "👨‍💻 تیم پشتیبانی به زودی با شما تماس خواهد گرفت.\n"
            
            reply_text += (
                f"━━━━━━━━━━━━━━━\n\n"
                f"✅ سوال دیگری دارید؟ از منوی زیر استفاده کنید."
            )
            
            self.send_message(chat_id, reply_text)
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            self.send_message(
                chat_id,
                "❌ متأسفانه خطایی در پردازش پیام رخ داد. لطفاً دوباره تلاش کنید."
            )
        
        # Show categories menu again
        self.show_categories_menu(chat_id)


# Singleton instance
telegram_bot = TelegramBot()