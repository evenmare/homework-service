import pytest

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model


def _get_credentials():
    username = 'user'
    password = 'S0meVeryHardPASSWORD.'

    user, created = get_user_model().objects.get_or_create(username=username)

    if created:
        user.set_password(password)
        user.save()

    return {'username': username, 'password': password}


@pytest.fixture()
def auth_credentials():
    """ Создание пользователя для авторизации """
    yield _get_credentials()


@pytest.fixture()
async def async_auth_credentials():
    """ Асинхронное создание пользователя для авторизации """
    yield await sync_to_async(_get_credentials)()
