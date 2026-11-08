from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.security import hash_password
from app.db.base import Base
from app.models import CartItem, Product, User  # noqa: F401

INITIAL_PRODUCTS = [
    {
        "title": "Apple iPhone 15 Pro Max 256GB Titanium",
        "description": "Флагманський смартфон з титановим корпусом, процесором A17 Pro та інноваційною системою камер 48 МП.",
        "image": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=600&auto=format&fit=crop&q=80",
        "price": Decimal("54999.00"),
        "old_price": Decimal("59999.00"),
        "category": "Smartphones",
        "stock_quantity": 15,
        "is_active": True,
    },
    {
        "title": "Samsung Galaxy S24 Ultra 512GB Titanium Black",
        "description": "Ультрафлагман з вбудованим S Pen, процесором Snapdragon 8 Gen 3 for Galaxy та підтримкою Galaxy AI.",
        "image": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=600&auto=format&fit=crop&q=80",
        "price": Decimal("57999.00"),
        "old_price": Decimal("62999.00"),
        "category": "Smartphones",
        "stock_quantity": 10,
        "is_active": True,
    },
    {
        "title": "Apple MacBook Air 15 M3 16GB / 512GB Midnight",
        "description": "Тонкий і потужний ноутбук на базі чипа Apple M3 з приголомшливим 15.3-дюймовим дисплеєм Liquid Retina.",
        "image": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop&q=80",
        "price": Decimal("68999.00"),
        "old_price": Decimal("74999.00"),
        "category": "Laptops",
        "stock_quantity": 8,
        "is_active": True,
    },
    {
        "title": "ASUS ROG Zephyrus G16 OLED Eclipse Gray",
        "description": "Геймерський шедевр з процесором Intel Core Ultra 9, відеокартою RTX 4080 та OLED-дисплеєм 240 Гц.",
        "image": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=600&auto=format&fit=crop&q=80",
        "price": Decimal("99999.00"),
        "old_price": Decimal("109999.00"),
        "category": "Laptops",
        "stock_quantity": 5,
        "is_active": True,
    },
    {
        "title": "Sony WH-1000XM5 Black Wireless Headphones",
        "description": "Бездротові навушники преміум-класу з найкращим на ринку активним шумозаглушенням і підтримкою LDAC.",
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80",
        "price": Decimal("14499.00"),
        "old_price": Decimal("16999.00"),
        "category": "Audio",
        "stock_quantity": 20,
        "is_active": True,
    },
    {
        "title": "Apple Watch Ultra 2 GPS + Cellular 49mm",
        "description": "Найвитриваліший годинник Apple з титановим корпусом, яскравим дисплеєм 3000 ніт та двочастотним GPS.",
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80",
        "price": Decimal("38999.00"),
        "old_price": Decimal("41999.00"),
        "category": "Wearables",
        "stock_quantity": 12,
        "is_active": True,
    },
    {
        "title": "Apple iPad Pro 11 M4 256GB Space Black",
        "description": "Революційний iPad з чипом M4, дисплеєм Ultra Retina XDR Tandem OLED та невагомим корпусом.",
        "image": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=600&auto=format&fit=crop&q=80",
        "price": Decimal("46999.00"),
        "old_price": Decimal("49999.00"),
        "category": "Tablets",
        "stock_quantity": 7,
        "is_active": True,
    },
    {
        "title": "Apple AirPods Pro 2 with USB-C MagSafe Case",
        "description": "Культові вакуумні навушники з адаптивним звуком, активним шумозаглушенням та кейсом USB-C.",
        "image": "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=600&auto=format&fit=crop&q=80",
        "price": Decimal("9999.00"),
        "old_price": Decimal("11499.00"),
        "category": "Audio",
        "stock_quantity": 30,
        "is_active": True,
    },
    {
        "title": "Logitech MX Master 3S Wireless Performance Mouse",
        "description": "Еталон ергономіки та продуктивності: тихі кліки, сенсор 8000 DPI та електромагнітне коліщатко MagSpeed.",
        "image": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600&auto=format&fit=crop&q=80",
        "price": Decimal("4599.00"),
        "old_price": Decimal("4999.00"),
        "category": "Accessories",
        "stock_quantity": 25,
        "is_active": True,
    },
    {
        "title": "Google Pixel 8 Pro 128GB Obsidian",
        "description": "Смартфон від Google з процесором Google Tensor G3, камерою рівня Pro та функціями штучного інтелекту.",
        "image": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=600&auto=format&fit=crop&q=80",
        "price": Decimal("34999.00"),
        "old_price": Decimal("39999.00"),
        "category": "Smartphones",
        "stock_quantity": 9,
        "is_active": True,
    },
    {
        "title": "Marshall Stanmore III Bluetooth Speaker Black",
        "description": "Легендарна домашня акустика з фірмовим вінтажним дизайном Marshall, глибоким звуком та Bluetooth 5.2.",
        "image": "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=600&auto=format&fit=crop&q=80",
        "price": Decimal("15999.00"),
        "old_price": Decimal("17999.00"),
        "category": "Audio",
        "stock_quantity": 6,
        "is_active": True,
    },
    {
        "title": "Dell XPS 14 Core Ultra 7 / 32GB / RTX 4050",
        "description": "Преміальний ультрабук з безрамковим InfinityEdge OLED сенсорним екраном 3.2K та скляним тачпадом.",
        "image": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=600&auto=format&fit=crop&q=80",
        "price": Decimal("84999.00"),
        "old_price": Decimal("92999.00"),
        "category": "Laptops",
        "stock_quantity": 4,
        "is_active": True,
    },
]


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_maker() as session:
        # 1. Automatic catalog seed if database is empty
        prod_count_result = await session.execute(
            select(func.count(Product.id))
        )
        prod_count = prod_count_result.scalar_one()

        if prod_count == 0:
            for p_data in INITIAL_PRODUCTS:
                session.add(Product(**p_data))
            await session.commit()
            print(
                f"Seeded {len(INITIAL_PRODUCTS)} starter products into catalog."
            )

        # 2. Automatic admin user seed if missing
        admin_result = await session.execute(
            select(User).where(User.email == "alosi4ek@gmail.com")
        )
        if not admin_result.scalar_one_or_none():
            admin_user = User(
                email="alosi4ek@gmail.com",
                password_hash=hash_password("admin12345"),
                is_admin=True,
            )
            session.add(admin_user)
            await session.commit()
            print("Seeded default admin user: alosi4ek@gmail.com")
