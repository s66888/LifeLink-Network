import mysql.connector

db = mysql.connector.connect(

    host="mysql.railway.internal",

    user="root",

    password="HxxhioLJAJhaUOSKmUIwgAGbZxMhEgTO",

    database="railway",

    port=3306

)

cursor = db.cursor()