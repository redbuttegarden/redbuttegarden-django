from .base import *

DEBUG = False

environ.Env.read_env('.env.prod')

SECRET_KEY = env('SECRET_KEY')
