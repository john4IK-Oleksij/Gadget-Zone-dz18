from app.enums import Role
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.user import User


def can_manage_product(user: User, product: Product | None = None) -> bool:
    """
    Перевірка дозволу на керування товаром (створення, редагування, видалення).
    Дозволено лише користувачам з роллю admin або manager.
    """
    return user.role in (Role.admin, Role.manager)


def can_modify_cart(user: User, cart_item: CartItem) -> bool:
    """
    Захист від IDOR (Insecure Direct Object Reference):
    Користувач може змінювати чи видаляти лише власні позиції кошика.
    Адміністратор має доступ до всіх записів для підтримки клієнтів.
    """
    return user.role == Role.admin or cart_item.user_id == user.id
