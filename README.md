# دستیار هوشمند لید و پشتیبانی راستاد (MVP)

پروژه یک سرویس ساده مبتنی بر FastAPI است که پیام کاربران را دریافت، دسته‌بندی، و بر اساس دانش داخلی پاسخ می‌دهد. اطلاعات کاربر و مکالمات در دیتابیس ذخیره می‌شود.

## تکنولوژی‌ها
- **Backend:** Python 3.12 + FastAPI
- **Database:** PostgreSQL 
- **LLM:** Mock (قابل تعویض با Claude/OpenAI)
- **Containerization:** Docker + Docker Compose

## نصب و اجرا

### با Docker Compose (پیشنهادی)
```bash
docker-compose build
docker-compose up -d
```

### اجرای تست ها
برای اجرای تست اندپوینت ها با pytest از درون کانتینر:
```bash
docker exec -it rastad-job-application-app-1 bash
pytest test/test_endpoints.py
```