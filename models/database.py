import mysql.connector

db = mysql.connector.connect(

    host="yamabiko.proxy.rlwy.net",

    user="root",

    password="HxxhioLJAJhaUOSKmUIwgAGbZxMhEgTO",

    database="railway",

    port=57088,

    autocommit=True,

    connection_timeout=300

)

cursor = db.cursor()