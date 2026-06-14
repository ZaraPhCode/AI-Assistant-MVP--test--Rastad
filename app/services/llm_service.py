import logging
from app.config import LLM_PROVIDER, CLAUDE_API_KEY, OPENAI_API_KEY

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.provider = LLM_PROVIDER

    def generate_reply(self, intent: str, knowledge: str, user_message: str) -> str:
        if self.provider == "mock":
            return self._mock_reply(intent, knowledge)
        elif self.provider == "claude":
            return self._claude_reply(intent, knowledge, user_message)
        elif self.provider == "openai":
            return self._openai_reply(intent, knowledge, user_message)
        else:
            logger.warning(f"Unknown LLM provider: {self.provider}, falling back to mock")
            return self._mock_reply(intent, knowledge)

    def _mock_reply(self, intent: str, knowledge: str) -> str:
        if not knowledge:
            return "متأسفانه اطلاعات کافی برای پاسخ‌گویی ندارم. لطفاً با پشتیبانی تماس بگیرید."
        if intent == "vip_question":
            return f"خدمات VIP راستاد شامل: {knowledge}"
        elif intent == "exchange_registration":
            return f"برای ثبت‌نام در صرافی: {knowledge}"
        elif intent == "kol_collaboration":
            return f"برنامه همکاری KOL راستاد: {knowledge}"
        elif intent == "support_request":
            return "درخواست شما دریافت شد. تیم پشتیبانی به زودی با شما تماس خواهد گرفت."
        else:
            return f"اطلاعات مرتبط: {knowledge}" if knowledge else "درخواست شما دریافت شد."

    def _claude_reply(self, intent, knowledge, user_message):
        # TODO: replace with Anthropic API call
        return self._mock_reply(intent, knowledge)

    def _openai_reply(self, intent, knowledge, user_message):
        # TODO: replace with OpenAI API call
        return self._mock_reply(intent, knowledge)

llm_service = LLMService()