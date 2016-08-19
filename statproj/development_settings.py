# -*- coding: utf-8 -*-

from .settings import *

# Enable Connection Pooling
DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
DATABASES['default']['NAME'] = 'stat_db'
