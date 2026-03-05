from settings import ADMIN_IDS

def is_admin(user_id: int | None) -> bool:
    return bool(user_id) and user_id in ADMIN_IDS