import logging
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

KEYWORD_MAP = {
    "vip_question": [
        "vip", "خدمات ویژه", "سرویس ویژه", "تحلیل اختصاصی", "وی آی پی",
        "اشتراک ویژه", "اکانت ویژه", "پلن ویژه", "vip چیست", "خدمات vip"
    ],
    "exchange_registration": [
        "ثبت‌نام", "صرافی", "ثبت نام", "ساختن حساب", "احراز هویت",
        "ثبت‌نام در صرافی", "اکانت صرافی", "باز کردن حساب", "رجیستر",
        "register", "ساخت اکانت", "ایجاد حساب", "صرافی ثبت‌نام",
        "چطور ثبت‌نام کنم", "نحوه ثبت‌نام"
    ],
    "kol_collaboration": [
        "kol", "همکاری", "تولید محتوا", "همکاری در تولید",
        "key opinion leader", "اینفلوئنسر", "تاثیرگذار",
        "همکاری کنم", "همکاری دارم", "kol بشم", "همکاری با راستاد"
    ],
    "support_request": [
        "مشکل", "پرداخت", "عضویت", "فعال نشدن", "خطا", "پشتیبانی", "تماس",
        "پول", "هزینه", "خرید", "فعال نشد", "فعال نشده", "نمی‌تونم",
        "کار نمی‌کنه", "خطا داره", "ارور", "باگ", "قطعه", "مشکل دارم",
        "پشتیبانی می‌خوام", "کمک می‌خوام", "فوری", "لغو", "استرداد",
        "بازپرداخت", "تراکنش", "واریز", "برداشت", "شارژ", "موجودی",
        "مسدود", "غیرفعال", "اکانت مسدود", "وصل نیست", "قطعه",
        "اشتراک", "تمدید", "نشد", "نمی‌شه", "نمیشه"
    ],
    "general_info": [
        "راستاد", "خدمات", "trade assist", "دستیار معاملاتی",
        "چیست", "چیه", "توضیح", "معرفی", "درباره", "امکانات",
        "قابلیت", "سرویس", "محصول", "پلتفرم"
    ],
}

SEGMENT_MAP = {
    "vip_question": "vip_interest",
    "exchange_registration": "exchange_signup",
    "kol_collaboration": "kol_candidate",
    "support_request": "support_needed",
    "general_info": "general_question",
    "unknown": "new_user",
}

def classify_message(message: str) -> tuple[str, str, bool]:
    """تشخیص intent, segment و نیاز به پشتیبانی انسانی
    
    Flow:
    1. Try rule-based keyword matching first (fast, no API cost)
    2. If not matched AND LLM provider is not mock:
       → Call LLM (Claude/OpenAI) to detect intent
    3. Map intent to segment
    4. Determine if human support is needed
    """
    intent = "unknown"
    message_lower = message.lower()
    
    # Step 1: Rule-based keyword matching
    for key, keywords in KEYWORD_MAP.items():
        if any(kw in message_lower for kw in keywords):
            intent = key
            logger.info(f"Intent detected via rule-based: {intent}")
            break

    # Step 2: Fallback to LLM if rule-based failed and LLM is available
    if intent == "unknown" and llm_service.provider != "mock":
        logger.info("Rule-based failed, falling back to LLM for intent detection")
        intent = _classify_with_llm(message)

    # Step 3: Map intent to segment
    segment = SEGMENT_MAP.get(intent, "new_user")
    
    # Step 4: Determine if human support is needed
    needs_human = intent in ["support_request", "unknown"]
    
    logger.info(f"Final classification - intent: {intent}, segment: {segment}, needs_human: {needs_human}")
    return intent, segment, needs_human

def _classify_with_llm(message: str) -> str:
    """Use LLM service to detect intent when rule-based fails
    
    This function is called when:
    - Rule-based keyword matching returned "unknown"
    - LLM_PROVIDER is set to "claude" or "openai" (not "mock")
    
    The LLM service handles:
    - Calling Claude API / OpenAI API
    - Graceful fallback to "unknown" on error
    - Logging the result
    """
    try:
        intent = llm_service.detect_intent(message)
        logger.info(f"LLM detected intent: {intent}")
        return intent
    except Exception as e:
        logger.error(f"LLM intent detection failed: {e}")
        return "unknown"