class BaseConfig:
    SECRET_KEY = 'B!1w8NAt1T^%kvhUI*S^'
    JWT_SECRET_KEY = 'T3OPEC9EK64BPYkV5axo6iJaE9TOoeK1isKoFni3Wm4'
class DevelopmentConfig(BaseConfig):
    DEBUG = True

config = {
    'development': DevelopmentConfig
}
