from app.enums import Role
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.user import User


def can_manage_product(user: User, product: Product | None = None) -> bool:
    """Загальна перевірка доступу до товарів для персоналу (адмін або менеджер)."""
    return user.role in (Role.admin, Role.manager)


def can_create_product(user: User) -> bool:
    """Створювати нові товари можуть як адмін, так і менеджер."""
    return user.role in (Role.admin, Role.manager)


def can_edit_product(user: User, product: Product | None = None) -> bool:
    """Редагувати описи, ціни та залишки можуть адмін і менеджер."""
    return user.role in (Role.admin, Role.manager)


def can_delete_product(user: User, product: Product | None = None) -> bool:
    """
    Видаляти товари з системи має право ВИКЛЮЧНО адміністратор.
    Менеджер не може видаляти товари, щоб уникнути випадкової втрати даних.
    """
    return user.role == Role.admin


def can_modify_cart(user: User, cart_item: CartItem) -> bool:
    """
    Конфіденційність та захист від IDOR:
    Кошик є суто персональним. Тільки сам власник (авторизований покупець)
    має право бачити, додавати чи видаляти позиції зі свого кошика.
    Навіть адміністратор не має доступу до чужого приватного кошика.
    """
    return cart_item.user_id == user.id
