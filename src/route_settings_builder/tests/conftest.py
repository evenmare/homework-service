import pytest

from django.contrib.auth import get_user_model


@pytest.fixture()
def auth_credentials():
    """ Создание пользователя для авторизации """
    username = 'user'
    password = 'S0meVeryHardPASSWORD.'

    user, created = get_user_model().objects.get_or_create(username=username)

    if created:
        user.set_password(password)
        user.save()

    yield {'username': username, 'password': password}
