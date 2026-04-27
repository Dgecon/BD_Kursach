from dotenv import load_dotenv
import os
from tkinter import *
from tkinter import ttk
import psycopg2
load_dotenv()
db_host = os.getenv("DATABASE_HOST")
db_name = os.getenv("DATABASE_NAME")
db_user = os.getenv("DATABASE_USER")        
db_password = os.getenv("DATABASE_PASSWORD")
db_port = os.getenv("DATABASE_PORT")
conn = psycopg2.connect(
    dbname=db_name,
    host=db_host,
    user=db_user,
    password=db_password,
    port=db_port
)
conn.autocommit = True
query = "select * from employee;"
cursor = conn.cursor()
cursor.execute(query)
records = cursor.fetchall()
root = Tk()
root.title("TaxiManager")
root.geometry("400x400")
mkrep = ttk.Button(text="Сформировать отчёт", command=lambda: print(records))
mkrep.grid(row=1,column=1)
listbox = Listbox(root)
listbox.grid(row=2,column=1)
for record in records:
    listbox.insert(END, record)
root.mainloop()