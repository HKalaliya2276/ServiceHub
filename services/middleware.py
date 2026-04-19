import json
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from users.models import User
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user(scope):
    try:
        user_id = scope['session']['_auth_user_id']
        return User.objects.get(id=user_id)
    except:
        return AnonymousUser()

class AuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'websocket':
            user = await get_user(scope)
            scope['user'] = user

        return await super().__call__(scope, receive, send)

def AuthMiddlewareStack(inner):
    return AuthMiddleware(inner)
