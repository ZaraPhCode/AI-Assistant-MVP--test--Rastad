import logging
import json
from typing import Optional
from app.config import LLM_PROVIDER, CLAUDE_API_KEY, OPENAI_API_KEY

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.provider = LLM_PROVIDER
        self._claude_client = None
        self._openai_client = None
        
        # Initialize clients if API keys are provided
        if CLAUDE_API_KEY and self.provider == "claude":
            try:
                import anthropic
                self._claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
                logger.info("Claude client initialized successfully")
            except ImportError:
                logger.error("anthropic package not installed. Install with: pip install anthropic")
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}")
        
        if OPENAI_API_KEY and self.provider == "openai":
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=OPENAI_API_KEY)
                logger.info("OpenAI client initialized successfully")
            except ImportError:
                logger.error("openai package not installed. Install with: pip install openai")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

    def generate_reply(self, intent: str, knowledge: str, user_message: str) -> str:
        """تولید پاسخ بر اساس intent و دانش بازیابی‌شده"""
        if self.provider == "mock" or (not CLAUDE_API_KEY and not OPENAI_API_KEY):
            return self._mock_reply(intent, knowledge)
        elif self.provider == "claude":
            return self._claude_reply(intent, knowledge, user_message)
        elif self.provider == "openai":
            return self._openai_reply(intent, knowledge, user_message)
        else:
            logger.warning(f"Unknown LLM provider: {self.provider}, falling back to mock")
            return self._mock_reply(intent, knowledge)

    def detect_intent(self, message: str) -> str:
        """تشخیص intent با استفاده از LLM"""
        if self.provider == "claude" and self._claude_client:
            return self._claude_detect_intent(message)
        elif self.provider == "openai" and self._openai_client:
            return self._openai_detect_intent(message)
        return "unknown"

    # ------------------------------------------------------------------
    # Mock implementations (fallback)
    # ------------------------------------------------------------------
    
    def _mock_reply(self, intent: str, knowledge: str) -> str:
        """پاسخ mock بر اساس intent"""
        if not knowledge:
            return "متأسفانه اطلاعات کافی برای پاسخ‌گویی ندارم. لطفاً با پشتیبانی تماس بگیرید."
        
        if intent == "vip_question":
            return f"خدمات VIP راستاد شامل: {knowledge}"
        elif intent == "exchange_registration":
            return f"برای ثبت‌نام در صرافی می‌توانید طبق راهنما اقدام کنید: {knowledge}"
        elif intent == "kol_collaboration":
            return f"برنامه همکاری KOL راستاد: {knowledge}"
        elif intent == "support_request":
            return "درخواست شما دریافت شد. تیم پشتیبانی به زودی با شما تماس خواهد گرفت."
        else:
            return f"اطلاعات مرتبط: {knowledge}" if knowledge else "درخواست شما دریافت شد."

    # ------------------------------------------------------------------
    # Claude API implementations
    # ------------------------------------------------------------------
    
    def _claude_reply(self, intent: str, knowledge: str, user_message: str) -> str:
        """تولید پاسخ با Claude API"""
        if not self._claude_client:
            logger.warning("Claude client not initialized, falling back to mock")
            return self._mock_reply(intent, knowledge)
        
        try:
            system_prompt = self._build_system_prompt(intent, knowledge)
            
            message = self._claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"پیام کاربر: {user_message}\n\nلطفاً بر اساس اطلاعات موجود در دانش پایه، یک پاسخ مفید و دقیق به فارسی ارائه بده."
                    }
                ]
            )
            
            reply = message.content[0].text
            logger.info(f"Claude reply generated for intent: {intent}")
            return reply
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return self._mock_reply(intent, knowledge)

    def _claude_detect_intent(self, message: str) -> str:
        """تشخیص intent با Claude"""
        if not self._claude_client:
            return "unknown"
        
        try:
            response = self._claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=50,
                temperature=0,
                system="شما یک سیستم طبقه‌بندی intent هستید. فقط یکی از موارد زیر را برگردانید: vip_question, exchange_registration, kol_collaboration, support_request, general_info, unknown",
                messages=[
                    {
                        "role": "user",
                        "content": f"پیام کاربر: {message}\n\nintent را تشخیص بده و فقط کلمه مربوطه را برگردان."
                    }
                ]
            )
            
            intent = response.content[0].text.strip().lower()
            valid_intents = ["vip_question", "exchange_registration", "kol_collaboration", "support_request", "general_info", "unknown"]
            
            if intent not in valid_intents:
                intent = "unknown"
            
            logger.info(f"Claude detected intent: {intent}")
            return intent
            
        except Exception as e:
            logger.error(f"Claude intent detection error: {e}")
            return "unknown"

    def _build_system_prompt(self, intent: str, knowledge: str) -> str:
        """ساخت system prompt برای Claude بر اساس intent و دانش"""
        base_prompt = """شما دستیار هوشمند شرکت راستاد هستید، یک شرکت مهندسی بازارهای سرمایه با بیش از ۸ سال سابقه.
وظیفه شما پاسخگویی دقیق، مفید و حرفه‌ای به کاربران فارسی‌زبان است.

قوانین:
1. همیشه به فارسی پاسخ بده.
2. پاسخ‌ها باید دقیق و بر اساس اطلاعات داده شده باشد.
3. اگر اطلاعات کافی نداری، مودبانه به کاربر بگو و پیشنهاد بده با پشتیبانی تماس بگیرد.
4. لحن پاسخ‌ها حرفه‌ای، گرم و کمک‌کننده باشد.
5. از اطلاعات دانش پایه که در اختیارت قرار می‌گیرد استفاده کن."""

        intent_guidance = {
            "vip_question": "\n\nاین کاربر درباره خدمات VIP سوال دارد. مزایا و خدمات ویژه را توضیح بده و در صورت تمایل کاربر را به ثبت‌نام تشویق کن.",
            "exchange_registration": "\n\nاین کاربر نیاز به راهنمایی برای ثبت‌نام در صرافی دارد. مراحل را به صورت گام‌به‌گام توضیح بده.",
            "kol_collaboration": "\n\nاین کاربر به همکاری به عنوان KOL علاقه‌مند است. شرایط و مزایای برنامه را توضیح بده.",
            "support_request": "\n\nاین کاربر مشکل یا درخواست پشتیبانی دارد. همدردی کن و اطمینان بده که به زودی بررسی می‌شود. اطلاعات تماس پشتیبانی را بده.",
            "general_info": "\n\nاین کاربر سوال عمومی درباره خدمات دارد. بر اساس دانش پایه پاسخ بده.",
            "unknown": "\n\nاین کاربر سوالی پرسیده که در دسته‌بندی‌های معمول نیست. بهترین پاسخ ممکن را بر اساس دانش پایه بده."
        }
        
        guidance = intent_guidance.get(intent, "")
        
        knowledge_section = f"\n\nاطلاعات دانش پایه:\n{knowledge}" if knowledge else "\n\nدانش پایه در دسترس نیست."
        
        return base_prompt + guidance + knowledge_section


# Singleton instance
llm_service = LLMService()