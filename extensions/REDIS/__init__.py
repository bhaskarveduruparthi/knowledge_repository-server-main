from flask_caching import Cache

redis = Cache()


def init_app(app):
    redis.init_app(app)