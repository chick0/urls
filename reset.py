from sqlite3 import connect

db = connect("urls/urls.db")

query_list = [
    "DROP TABLE IF EXISTS `urls`;",
    "CREATE TABLE urls ("
    "  code  varchar(20),"
    "  url   varchar(2000),"
    "  magic char(256)"
    ");",
    "CREATE UNIQUE INDEX urls_code_U ON urls(code);"
]

cur = db.cursor()
for query in query_list:
    cur.execute(query)

db.commit()
db.close()

print("database_reset_ok")
