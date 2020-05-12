from app.db.user import User
from app.db.general import save_user, get_user_by_email


def create_user(email, password, first_name, last_name, institution):
    user = User(email=email, first_name=first_name, last_name=last_name, institution=institution, trusted=0)
    user.set_password(password)
    save_user(user)
    return user


def check_user(email, password):
    user = get_user_by_email(email)

    if not user or not user.check_password(password):
        return None
    return user
