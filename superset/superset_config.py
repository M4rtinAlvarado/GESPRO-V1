
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
}
SESSION_COOKIE_SAMESITE = None
SESSION_COOKIE_SECURE = False # Usar False en desarrollo HTTP
CSRF_COOKIE_SAMESITE = None


X_FRAME_OPTIONS = None
TALISMAN_ENABLED = False
ENABLE_CORS = True
PUBLIC_ROLE_LIKE_GAMMAS = True # Puede ayudar en la visualización

CORS_ALLOW_HEADERS = [
    "Authorization",
    "Content-Type",
    "X-CSRFToken",
    "X-Requested-With",
]
CORS_ALLOW_ORIGINS = [

    "http://localhost:3003" # Añadimos localhost por seguridad en desarrollo
]
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]


SECRET_KEY = '65xo4J3AvtbK1A' 