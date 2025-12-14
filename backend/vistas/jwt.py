import os
import jwt
import datetime

GUEST_SECRET = os.environ.get("SUPERSET_GUEST_JWT_SECRET")

def generar_guest_token(user, dashboard_id):
    if user.is_anonymous:
        username = "guest"
        first_name = "Invitado"
        last_name = ""
    else:
        username = user.username
        first_name = user.first_name or ""
        last_name = user.last_name or ""

    payload = {
        "user": {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
        },
        "resources": [{"type": "dashboard", "id": str(dashboard_id)}],
        "rls": [],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=int(os.environ.get("GUEST_TOKEN_EXPIRATION", 3600)))
    }

    return jwt.encode(payload, GUEST_SECRET, algorithm="HS256")
