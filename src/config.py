class BaseConfig:
    SECRET_KEY = 'B!1w8NAt1T^%kvhUI*S^'

class DevelopmentConfig(BaseConfig):
    DEBUG = True

config = {
    'development': DevelopmentConfig
}
