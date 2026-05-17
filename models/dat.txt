import mysql.connector

db = mysql.connector.connect(

    host="localhost",
    user="root",
    password="1630",
    database="lifelink"

)

cursor = db.cursor()