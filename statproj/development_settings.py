# -*- coding: utf-8 -*-

from .settings import *

# Enable Connection Pooling
DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
DATABASES['default']['NAME'] = 'stat_db'


redis_url = urlparse.urlparse(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
CACHES = {
    "default": {
         "BACKEND": "redis_cache.RedisCache",
         "LOCATION": "{0}:{1}".format(redis_url.hostname, redis_url.port),
         "OPTIONS": {
             "PASSWORD": redis_url.password,
             "DB": 0,
         }
    }
}
