from tkinter import *
from tkinter import ttk
import psycopg2
root = Tk()
root.title("TaxiManager")
root.geometry("400x400")
mkrep = ttk.Button(text="Сформировать отчёт")
mkrep.grid(row=1,column=1)
root.mainloop()