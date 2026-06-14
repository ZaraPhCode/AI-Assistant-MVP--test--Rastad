# دستیار هوشمند لید و پشتیبانی راستاد (MVP)

پروژه یک سرویس ساده مبتنی بر FastAPI است که پیام کاربران را دریافت، دسته‌بندی، و بر اساس دانش داخلی پاسخ می‌دهد. اطلاعات کاربر و مکالمات در دیتابیس ذخیره می‌شود.

## تکنولوژی‌ها
- **Backend:** Python 3.11 + FastAPI
- **Database:** PostgreSQL (قابل تعویض با SQLite)
- **LLM:** Mock (قابل تعویض با Claude/OpenAI)
- **Containerization:** Docker + Docker Compose

## نصب و اجرا

### با Docker Compose (پیشنهادی)
```bash
docker-compose up --build