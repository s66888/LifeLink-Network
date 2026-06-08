def get_db_connection():

    return mysql.connector.connect(

        host="localhost",

        user="root",

        password="1630",

        database="lifelink"

    )