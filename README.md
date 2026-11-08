# Gadget Zone (DZ-18)

Повноцінний E-Commerce інтернет-магазин на базі **FastAPI (асинхронний бекенд)** та **Vanilla JavaScript / HTML5 / CSS3 (BEM) фронтенду**.

Проєкт розроблено як еталонну архітектуру (Золотий стандарт) сучасного веб-додатку із суворим дотриманням безпеки, рольової моделі (RBAC) та готовністю до хмарного деплою.

---

## 🔗 Репозиторій

* **GitHub:** [https://github.com/john4IK-Oleksij/Gadget-Zone-dz18.git](https://github.com/john4IK-Oleksij/Gadget-Zone-dz18.git)

---

## 📚 Архітектурна Документація (Золотий Стандарт)

* **[mission-backend.md](mission-backend.md)** (або `mission.md`) — Повна інженерна специфікація бекенду:
  * Layered Clean Architecture (Router ➔ Dependency ➔ Service ➔ Model).
  * Двотокенна безпека JWT (Access 15m + Refresh 7d) з `HttpOnly` Cookie.
  * E-Commerce Soft Delete (зняття з продажу замість фізичного видалення).
  * Гайд із хмарного деплою на Railway (MySQL, Volumes, динамічний `PORT`).
* **[mission_front.md](mission_front.md)** — Повна інженерна специфікація фронтенду:
  * Поітераційний чеклист реалізації (12 ітерацій).
  * Дизайн-система за правилом 60/30/10 (Cream, Dark Green, Green, Mustard Gold, Burgundy).
  * Липкий хедер (`header-sticky`) та індикатор здоров'я API (Health Dot).
  * Серверна пагінація, кінематографічний плавний скрол (750ms `easeInOutCubic`), керування клавішами ⬅️/➡️ та жести захвату (Mouse Grab & Touch Swipe).
  * Тихе автооновлення сесії (Silent Refresh) та 5-хвилинний захист від бездіяльності (Inactivity Guard).
* **[front/specs/iteration-checklist.md](front/specs/iteration-checklist.md)** — Детальний чеклист приймального тестування ітерацій.

---

## 🏗 Структура Проєкту

```text
Gadget-Zone-dz18/
├── app/                        # Асинхронний бекенд (FastAPI + SQLAlchemy 2.0)
│   ├── api/                    # Тонкі роутери (admin, auth, cart, products, users)
│   ├── core/                   # Конфігурація (.env), винятки, JWT безпека (pwdlib)
│   ├── db/                     # Async engine (aiomysql), sessionmaker, ініціалізація
│   ├── dependencies/           # PEP 593 Annotated залежності (DbSession, CurrentUser, AdminUser)
│   ├── models/                 # Декларативні ORM моделі (User, Product, CartItem)
│   ├── schemas/                # Валідація DTO (Pydantic v2)
│   └── services/               # Бізнес-логіка (AdminService, CartService, ProductService)
├── front/                      # Vanilla JS фронтенд (без фреймворків та бандлерів)
│   ├── css/                    # Модульні BEM-стилі (base, layout, components, responsive)
│   ├── js/                     # ES Модулі (api, auth, header, cart, products, admin, inactivity)
│   ├── specs/                  # Специфікації та чеклисти ітерацій
│   ├── static/                 # Фавіконки та статичні ассети
│   ├── index.html              # Вітрина магазину (Shop / Каталог з пагінацією та жестами)
│   ├── details.html            # Детальна картка товару
│   ├── cart.html               # Кошик покупця зі статусами наявності та «Знято з продажу»
│   ├── login.html              # Вхід та реєстрація (Sign In / Sign Up)
│   └── admin.html              # Адміністративна зона (Дашборд, Реєстр користувачів, Товари)
├── migrations/                 # Міграції бази даних (Alembic)
├── tests/                      # Інтеграційні тести (Pytest-Asyncio, 100% Green)
├── uploads/                    # Медіафайли товарів (підтримка Railway Volumes)
├── mission-backend.md          # Архітектурна специфікація бекенду
├── mission_front.md            # Архітектурна специфікація фронтенду
├── pyproject.toml              # Конфігурація pytest-asyncio для Windows / Linux
├── requirements.txt            # Фіксовані залежності для деплою
├── railway.json                # Конфігурація білду та запуску на Railway
├── Procfile                    # Стартова команда Uvicorn
└── README.md                   # Головна документація проєкту
```

---

## 🚀 Швидкий Старт (Локально)

### 1. Бекенд:
1. Створіть та активуйте віртуальне оточення:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```
2. Встановіть залежності:
   ```bash
   pip install -r requirements.txt
   ```
3. Створіть файл `.env` у корені проєкту:
   ```ini
   DATABASE_URL=mysql+aiomysql://root:password@127.0.0.1:3306/gadget_zone_db
   JWT_SECRET_KEY=your_secret_key_here
   ACCESS_TOKEN_TTL_MINUTES=15
   REFRESH_TOKEN_TTL_DAYS=7
   ```
4. Запустіть сервер:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   * Документація Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Фронтенд:
* Відкрийте папку `front/` через розширення **VS Code Live Server** (порт `5500`):
  [http://127.0.0.1:5500/front/index.html](http://127.0.0.1:5500/front/index.html)
* *Або відкрийте безпосередньо через FastAPI:* [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### 3. Тестування:
Запуск усього набору інтеграційних тестів:
```bash
python -m pytest
```

---

## ☁️ Деплой на Railway (Hobby Plan)

1. Запушіть репозиторій на GitHub.
2. Створіть новий проєкт на [railway.com](https://railway.com/) ➔ **Deploy from GitHub repo**.
3. Додайте плагін **MySQL** (`Add MySQL`).
4. У вкладці **Variables** бекенд-сервісу додайте:
   * `DATABASE_URL` = `${{MySQL.DATABASE_URL}}` (автоматично конвертується у `mysql+aiomysql://`).
   * `JWT_SECRET_KEY` = `<ваш_секретний_ключ>`.
5. У вкладці **Volumes** підключіть постійний SSD-диск із точкою монтування:
   `/app/uploads`
6. У вкладці **Settings** ➔ **Networking** натисніть **Generate Domain**. Магазин одразу доступний у мережі!
