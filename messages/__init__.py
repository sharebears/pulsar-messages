from werkzeug import find_modules, import_string

from messages import routes


def init_app(app):
    with app.app_context():
        for name in find_modules('messages', recursive=True):
            import_string(name)
        app.register_blueprint(routes.bp)
