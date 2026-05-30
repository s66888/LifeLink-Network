

import mysql.connector
from mysql.connector import pooling


connection_pool = pooling.MySQLConnectionPool(

    pool_name="lifelink_pool",

    pool_size=5,

    host="yamabiko.proxy.rlwy.net",

    user="root",

    password="HxxhioLJAJhaUOSKmUIwgAGbZxMhEgTO",

    database="railway",

    port=57088,

    autocommit=True,

    connection_timeout=10
)


def get_db_connection():

    return connection_pool.get_connection()