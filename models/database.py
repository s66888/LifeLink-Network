import mysql.connector

db = mysql.connector.connect(

    host="yamabiko.proxy.rlwy.net",

    user="root",

    password="HxxhioLJAJhaUOSKmUIwgAGbZxMhEgTO",

    database="railway",

    port=57088

)

cursor = db.cursor()