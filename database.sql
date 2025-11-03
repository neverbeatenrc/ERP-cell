import mysql.connector
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="yourpassword",
    database="erp_db"
)
cursor = conn.cursor()


