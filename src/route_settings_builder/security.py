from typing import Optional, Any

from asgiref import sync

from django.http import HttpRequest
from django.contrib import auth

from ninja.security import HttpBasicAuth


class HttpBasicDjangoAuth(HttpBasicAuth):
    """ Basic Auth w/ username and password """

    def authenticate(
        self, request: HttpRequest, username: str, password: str
    ) -> Optional[Any]:
        user = auth.authenticate(request, username=username, password=password)

        if user and user.is_active:
            return user

        return None


class AsyncHttpBasicDjangoAuth(HttpBasicDjangoAuth):
    """ Basic Auth w/ username and password (для асинхронных запросов) """

    @sync.sync_to_async
    def authenticate(
        self, request: HttpRequest, username: str, password: str
    ) -> Optional[Any]:
        return super().authenticate(request, username, password)
