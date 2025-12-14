# 🧠 Global AI Content Empire

منصة أتمتة مركزية لإدارة شبكة من المواقع المتخصصة (10-50+ موقع) من لوحة تحكم واحدة.

## ✨ المميزات

- **جلب المحتوى**: RSS feeds + Playwright stealth scraping
- **كشف التكرار الدلالي**: ChromaDB مع 80% similarity threshold
- **معالجة AI**: Gemini Flash (أساسي) → Groq Llama (احتياطي)
- **خط أنابيب الصور**: Source → Stock → Bing DALL-E → Flux-Schnell
- **علامات مائية تلقائية**: Pillow
- **نشر تلقائي**: WordPress REST API
- **لوحة تحكم عربية RTL**: React + Tailwind

## 🚀 التشغيل السريع

### 1. نسخ ملف البيئة
```bash
cp .env.example .env
```

### 2. تعديل المتغيرات
```env
GEMINI_API_KEY=your-key
GROQ_API_KEY=your-key
PEXELS_API_KEY=your-key
ENCRYPTION_KEY=your-fernet-key
```

### 3. توليد مفتاح التشفير
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### 4. تشغيل Docker
```bash
docker-compose up -d
```

### 5. الوصول
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📁 هيكل المشروع

```
empire/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI endpoints
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── tasks/           # Celery tasks
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/      # React components
│       ├── pages/           # Page components
│       └── i18n/            # Translations
└── nginx/
```

## 🔧 الخدمات

| الخدمة | المنفذ | الوصف |
|--------|--------|-------|
| Backend | 8000 | FastAPI + Celery |
| Frontend | 3000 | React Dashboard |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Task Queue |
| ChromaDB | 8001 | Vector Store |
| Nginx | 80 | Reverse Proxy |

## 📝 استخدام الـ API

### إضافة موقع
```bash
curl -X POST http://localhost:8000/api/sites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "موقع تجريبي",
    "url": "https://example.com",
    "wp_username": "admin",
    "wp_app_password": "xxxx xxxx xxxx",
    "target_language": "ar",
    "velocity_mode": "news"
  }'
```

### إضافة مصدر RSS
```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": "uuid-here",
    "name": "Aljazeera",
    "type": "rss",
    "url": "https://aljazeera.net/rss"
  }'
```

## 🔄 Celery Tasks

- **poll_all_sources**: كل 10 دقائق (أخبار) / 24 ساعة (evergreen)
- **process_article**: معالجة المقال عبر AI + Image Pipeline
- **cleanup_old_articles**: تنظيف يومي

## 📄 License

MIT
