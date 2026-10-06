import hashlib
import secrets

from flask import request
from repositories import user_repository


def generate_agent_token():
    return secrets.token_urlsafe(32)


def hash_agent_token(token):
    return hashlib.sha256(str(token).encode('utf-8')).hexdigest()


def save_agent_token(user_id, token):
    return user_repository.set_agent_token(user_id, hash_agent_token(token))


def get_agent_user():
    auth = request.headers.get('Authorization', '')
    if not auth.lower().startswith('bearer '):
        return None
    token = auth.split(' ', 1)[1].strip()
    if not token:
        return None
    user = user_repository.get_by_agent_token(hash_agent_token(token))
    if not user or not user.get('active', True):
        return None
    return user
