# دستیار هوشمند لید و پشتیبانی راستاد (MVP)

<div dir="rtl">

پروژه‌ای مبتنی بر **FastAPI** که به عنوان یک دستیار هوشمند برای مدیریت پیام‌های کاربران، دسته‌بندی خودکار درخواست‌ها (Intent Classification)، تشخیص سگمنت کاربر، و پاسخ‌دهی هوشمند بر اساس **دانش داخلی راستاد** طراحی شده است. این سیستم می‌تواند با **Claude API** (Anthropic) یا به صورت **Mock** کار کند و آماده اتصال به ربات تلگرام، CRM و دیگر کانال‌های ارتباطی است.

---

## فهرست مطالب
- [معماری و ساختار پروژه](#-معماری-و-ساختار-پروژه)
- [تکنولوژی‌های استفاده شده](#-تکنولوژی‌های-استفاده-شده)
- [منطق پردازش پیام](#-منطق-پردازش-پیام)
- [نصب و اجرا](#-نصب-و-اجرا)
- [API Endpoints](#-api-endpoints)
- [نمونه Request و Response](#-نمونه-request-و-response)
- [تست پروژه](#-تست-پروژه)
- [ویژگی‌های پیاده‌سازی شده (بر اساس معیارهای تسک)](#-ویژگی‌های-پیاده‌سازی-شده-بر-اساس-معیارهای-تسک)
- [موارد پیاده‌سازی نشده و دلایل](#-موارد-پیاده‌سازی-نشده-و-دلایل)
- [نحوه تعویض Mock با Claude واقعی](#-نحوه-تعویض-mock-با-claude-واقعی)
- [محدودیت‌ها و بهبودهای آتی](#-محدودیت‌ها-و-بهبودهای-آتی)

---

## معماری و ساختار پروژه

### ساختار پوشه‌ها
```
rastad-ai-assistant/
├── app/ # کد اصلی برنامه
│ ├── init.py
│ ├── main.py # نقطه ورود FastAPI، middlewareها، rate limiter
│ ├── config.py # تنظیمات و متغیرهای محیطی
│ ├── database.py # اتصال به دیتابیس (PostgreSQL/SQLite)
│ ├── models.py # مدل‌های SQLAlchemy (User, Message)
│ ├── schemas.py # Pydantic models برای validation
│ ├── routers/ # مسیرهای API
│ │ ├── messages.py # POST /message و POST /message-form
│ │ └── users.py # GET /users و GET /users/{id}/messages
│ ├── services/ # لایه منطق کسب‌وکار
│ │ ├── classifier.py # تشخیص intent و segment (rule-based + LLM fallback)
│ │ ├── knowledge_service.py # جستجو در فایل‌های دانش
│ │ └── llm_service.py # سرویس LLM (mock, claude, openai)
│ ├── knowledge_base/ # فایل‌های دانش داخلی راستاد
│ │ ├── rastad_services.txt
│ │ ├── vip_products.txt
│ │ ├── exchange_signup.txt
│ │ └── kol_program.txt
│ └── templates/ # قالب‌های HTML برای UI ساده تست
│ ├── base.html
│ ├── index.html
│ └── users.html
├── tests/ # تست‌های خودکار
│ └── test_endpoints.py
├── Dockerfile # تنظیمات Docker برای سرویس app
├── docker-compose.yml # Docker Compose (app + PostgreSQL database)
├── requirements.txt # وابستگی‌های Python
├── .env.example # نمونه فایل متغیرهای محیطی
├── .gitignore
├── pytest.ini # تنظیمات pytest
└── README.md # همین فایل
```

### نمودار جریان پردازش پیام

```text
User → [UI/API] → POST /api/message
↓
┌─────────────────┐
│ Validation │ ← Pydantic (required: user_id, name, message)
└────────┬────────┘
↓
┌─────────────────┐
│ Classifier │ ← Rule-based (keyword matching)
│ │ Fallback: Claude API (if enabled)
└────────┬────────┘
↓
┌─────────────────┐
│ Knowledge Base │ ← Keyword search in .txt files
│ │ Upgrade path: Vector DB (FAISS)
└────────┬────────┘
↓
┌─────────────────┐
│ LLM Service │ ← Mock: Template-based replies
│ │ Claude: Claude API call
│ │ Auto-fallback to mock on error
└────────┬────────┘
↓
┌─────────────────┐
│ Database │ ← Upsert User + Insert Message
│ PostgreSQL │
└────────┬────────┘
↓
┌─────────────────┐
│ Logging │ ← Log user_id, intent, segment, errors
└────────┬────────┘
↓
JSON response to user
```


## تکنولوژی‌های استفاده شده

| دسته | تکنولوژی | توضیح |
|------|----------|--------|
| **Backend Framework** | FastAPI 0.115 | async، سریع، با validation خودکار |
| **زبان برنامه‌نویسی** | Python 3.12 | |
| **دیتابیس** | PostgreSQL 15 |  |
| **ORM** | SQLAlchemy 2.0 | مدیریت migrations و queries |
| **Validation** | Pydantic 2.10 | اعتبارسنجی خودکار ورودی‌ها |
| **LLM Provider** | Claude API / Mock | قابل تعویض بدون تغییر کد |
| **Containerization** | Docker + Docker Compose | |
| **Web Server** | Uvicorn | ASGI server |
| **Testing** | pytest + TestClient | |
| **Templating** | Jinja2 | برای UI تست |
| **Search** | Keyword-based | (قابل ارتقا به FAISS) |

---

## منطق پردازش پیام

### 1️⃣ دریافت و اعتبارسنجی

وقتی یک پیام از طریق `POST /api/message` دریافت می‌شود:

**Validation (Pydantic):**
- `user_id`: نمی‌تواند خالی باشد (`min_length=1`)
- `name`: نمی‌تواند خالی باشد (`min_length=1`)
- `message`: نمی‌تواند خالی باشد (`min_length=1`)

در صورت عدم رعایت، خطای **422 Validation Error** برگردانده می‌شود.

### 2️⃣ تشخیص Intent و Segment

**سیستم Rule-based (کلیدواژه‌ای):**

| Intent | کلمات کلیدی | Segment |
|--------|-------------|---------|
| `vip_question` | vip, خدمات ویژه, سرویس ویژه, تحلیل اختصاصی | `vip_interest` |
| `exchange_registration` | ثبت‌نام, صرافی, ساختن حساب, احراز هویت | `exchange_signup` |
| `kol_collaboration` | kol, همکاری, تولید محتوا | `kol_candidate` |
| `support_request` | مشکل, پرداخت, عضویت, فعال نشدن, خطا, پشتیبانی | `support_needed` |
| `general_info` | راستاد, خدمات, trade assist, دستیار معاملاتی | `general_question` |
| `unknown` | (هیچ‌کدام) | `new_user` |

<div dir='rtl'>
**Fallback به Claude:**
</div>
اگر `LLM_PROVIDER=claude` باشد و rule-based نتواند intent را تشخیص دهد، پیام به Claude API ارسال می‌شود تا intent را تشخیص دهد.

### 3️⃣ جستجو در دانش داخلی (Knowledge Base)

سیستم کلمات پیام کاربر را با محتوای ۴ فایل متنی در `app/knowledge_base/` مقایسه می‌کند:

- `rastad_services.txt` — خدمات کلی راستاد
- `vip_products.txt` — خدمات ویژه
- `exchange_signup.txt` — راهنمای ثبت‌نام صرافی
- `kol_program.txt` — برنامه همکاری KOL

**روش جستجو:** Keyword matching (یافتن فایل‌هایی که حداقل یک کلمه مشترک با query دارند)

### 4️⃣ تولید پاسخ

#### حالت Mock (پیش‌فرض):
پاسخ‌ها بر اساس intent و دانش بازیابی‌شده ساخته می‌شوند:

```python
if intent == "vip_question":
    return f"خدمات VIP راستاد شامل: {knowledge}"
elif intent == "support_request":
    return "درخواست شما دریافت شد. تیم پشتیبانی به زودی با شما تماس خواهد گرفت."
```

### حالت Claude:
یک System Prompt فارسی با اطلاعات کامل از راستاد و دانش پایه ساخته می‌شود

پیام کاربر + System Prompt به Claude 3.5 Sonnet ارسال می‌شود

پاسخ تولیدشده برگردانده می‌شود

در صورت خطا (قطعی API، timeout)، به صورت خودکار به Mock fallback می‌کند

#### 5️⃣ ذخیره‌سازی
User (upsert):

اگر کاربر جدید باشد: ایجاد کاربر با segment تشخیص‌داده‌شده

اگر کاربر وجود داشته باشد: بروزرسانی name، segment و last_seen_at

#### Message:

ذخیره پیام کاربر، پاسخ دستیار، intent، needs_human_support

# نصب و اجرا
پیش‌نیازها
Docker و Docker Compose

(برای اجرای محلی: Python 3.12 + PostgreSQL)

### روش ۱: اجرا با Docker Compose (پیشنهادی)

```
# کلون کردن پروژه
git clone https://github.com/ZaraPhCode/AI-Assistant-MVP--test--Rastad.git
cd AI-Assistant-MVP--test--Rastad

# ساخت و اجرا
docker-compose build
docker-compose up -d

# بررسی وضعیت
docker-compose ps
```

سپس در مرورگر باز کنید: http://localhost:8000

UI تست در همین آدرس قابل دسترسی است.

### روش ۲: اجرای محلی (بدون Docker)

```
# نصب وابستگی‌ها
pip install -r requirements.txt

# تنظیم متغیرهای محیطی (کپی از .env.example)
cp .env.example .env
# فایل .env را با تنظیمات خود ویرایش کنید

# اجرا
uvicorn app.main:app --reload
```

### روش ۳: اجرای تست‌ها
از داخل کانتینر Docker:
```
docker exec -it rastad-job-application-app-1 bash
pytest tests/test_endpoints.py -v
```

اجرای یک تست خاص:
```
docker exec -it rastad-job-application-app-1 pytest tests/test_endpoints.py::test_vip_message -v
```

اجرای پنج تست اصلی:
```
docker exec -it rastad-job-application-app-1 pytest tests/test_endpoints.py -v -k "test_vip_message or test_exchange_registration or test_kol_collaboration or test_support_request or test_general_question"
```

# API Endpoints
`POST /api/message`  

پردازش پیام کاربر و دریافت پاسخ
Request Body:
```json
{
  "user_id": "12345",
  "name": "Ali",
  "message": "خدمات VIP راستاد چیست؟"
}
```

Response (200):
```json
{
  "reply": "خدمات VIP راستاد شامل: تحلیل‌های اختصاصی روزانه بازار، راهنمایی معاملاتی ویژه اعضا، ...",
  "intent": "vip_question",
  "user_segment": "vip_interest",
  "needs_human_support": false
}
```

`GET /api/users`  

لیست تمام کاربران ثبت‌شده

Response (200):
```json
[
  {
    "user_id": "12345",
    "name": "Ali",
    "segment": "vip_interest",
    "created_at": "2025-03-24T11:37:21",
    "last_seen_at": "2025-03-24T11:40:20"
  }
]
```

`GET /api/users/{user_id}/messages`  

تاریخچه پیام‌های یک کاربر خاص

Response (200):

```json
[
  {
    "id": 1,
    "user_id": "12345",
    "user_message": "خدمات VIP راستاد چیست؟",
    "assistant_reply": "خدمات VIP راستاد شامل...",
    "intent": "vip_question",
    "needs_human_support": false,
    "created_at": "2025-03-24T11:37:21"
  }
]
```
Error (404):

```json
{
  "detail": "User not found"
}
```

`GET /api/`

Health check

`GET /` و `GET /users-page`

UI ساده برای تست دستی

### نمونه Request و Response
تست ۱: سوال درباره خدمات VIP

```bash
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{"user_id":"12345","name":"Ali","message":"خدمات VIP راستاد چیست؟"}'
  ```

تست ۲: راهنمایی ثبت‌نام صرافی
```bash
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{"user_id":"67890","name":"Sara","message":"چطور در صرافی ثبت‌نام کنم؟"}'
  ```
تست ۳: درخواست همکاری KOL
```bash
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{"user_id":"11111","name":"Reza","message":"می‌خواهم KOL بشم"}'
  ```
تست ۴: مشکل پرداخت
```bash
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{"user_id":"22222","name":"Maryam","message":"پول دادم ولی اشتراکم فعال نشده"}'
  ```
تست ۵: سوال عمومی
```bash
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{"user_id":"33333","name":"Hossein","message":"Trade Assist چیست؟"}'
  ```

###   ❌ موارد پیاده‌سازی نشده و دلایل
##### ۱. احراز هویت (Authentication)
دلیل: طبق توضیحات تسک: "سیستم احراز هویت کامل لازم نیست"
در صورت نیاز، افزودن JWT یا OAuth2 با FastAPI بسیار ساده است.

##### ۲. ربات تلگرام
دلیل: محدودیت زمان (۲ روز). یک UI ساده مبتنی بر وب جایگزین شده است.
توجه: تجربه ساخت ربات تلگرام را دارم (پروژه Tradeboard). برای اتصال کافیست webhook تلگرام را به POST /api/message متصل کنم. پیاده‌سازی کامل آن حدود ۲-۳ ساعت زمان می‌برد.

##### ۳. Vector DB (FAISS / Chroma)
دلیل: جستجوی keyword-based نیازمندی‌های MVP را پوشش می‌دهد.
ارتقا به FAISS با افزودن sentence-transformers و index کردن فایل‌ها قابل انجام است.

##### ۴. Redis برای Rate Limiting
دلیل: Rate limit در حال حاضر in-memory پیاده‌سازی شده که برای MVP کافی است.
برای Production: جایگزینی با Redis + fastapi-limiter توصیه می‌شود.

##### ۵. CI/CD Pipeline
دلیل: طبق تسک: "CI/CD کامل لازم نیست"

##### ۶. احراز هویت / پرداخت / اتصال واقعی CRM
دلیل: همگی طبق تسک "لازم نیستند"

### نحوه تعویض Mock با Claude واقعی
سیستم به گونه‌ای طراحی شده که تنها با تغییر یک متغیر محیطی می‌توان از Mock به Claude API واقعی سوئیچ کرد:

مرحله ۱: دریافت API Key از Anthropic
مراجعه به https://console.anthropic.com

ثبت‌نام و دریافت API Key

مرحله ۲: تنظیم متغیرهای محیطی
فایل .env را ویرایش کنید:

env
```text
LLM_PROVIDER=claude
CLAUDE_API_KEY=sk-ant-api03-your-actual-key-here
```
مرحله ۳: راه‌اندازی مجدد
```bash
docker-compose down
docker-compose up -d
```
آنچه تغییر می‌کند:
بدون تغییر کد — سرویس llm_service.py به صورت خودکار کلاینت Claude را initialize می‌کند

System prompt فارسی با اطلاعات راستاد + دانش پایه ساخته می‌شود

پاسخ‌ها توسط Claude 3.5 Sonnet تولید می‌شود

در صورت خطای API، fallback خودکار به mock انجام می‌شود

### محدودیت‌ها و بهبودهای آتی

| محدودیت | دلیل | راه حل |
|--------|-------------|---------|
| جستجوی keyword-based	 | پیاده‌سازی سریع | Vector Search با FAISS + Sentence Transformers |
| Rate limit in-memory | MVP | Redis + fastapi-limiter |
| عدم احراز هویت | طبق تسک لازم نبود | JWT Authentication |
| پاسخ‌های mock با تنوع کم | حالت mock | فعال‌سازی Claude API |
| `general_info` | راستاد, خدمات, trade assist, دستیار معاملاتی | `general_question` |
| `unknown` | (هیچ‌کدام) | `new_user` |
