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
    """تشخیص intent, segment و نیاز به پشتیبانی انسانی"""
    intent = "unknown"
    message_lower = message.lower()
    
    # Priority matching - check support first (it has higher priority)
    for key, keywords in KEYWORD_MAP.items():
        if any(kw in message_lower for kw in keywords):
            intent = key
            break

    # fallback to LLM if available and not mock
    if intent == "unknown" and llm_service.provider != "mock":
        intent = _classify_with_llm(message)

    segment = SEGMENT_MAP.get(intent, "new_user")
    needs_human = intent in ["support_request", "unknown"]
    return intent, segment, needs_human

def _classify_with_llm(message: str) -> str:
    # placeholder for LLM-based intent detection
    return "unknown"