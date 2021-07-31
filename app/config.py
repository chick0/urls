from os import environ

# SQLALCHEMY
SQLALCHEMY_DATABASE_URI = environ.get("urls_sql", default="sqlite:///urls.sqlite")
SQLALCHEMY_TRACK_MODIFICATIONS = False
