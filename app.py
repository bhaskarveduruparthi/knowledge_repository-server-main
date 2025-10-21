from __init__ import Create_app


if __name__ == '__main__':
    create_app = Create_app()
    create_app.run(debug=True)
else:
    gunicorn_app = Create_app()
