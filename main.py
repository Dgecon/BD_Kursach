from dotenv import load_dotenv
import os, sys
from tkinter import *
from tkinter import ttk, messagebox
import psycopg2
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as ticker

load_dotenv()
conn = psycopg2.connect(
    dbname=os.getenv("DATABASE_NAME"),
    host=os.getenv("DATABASE_HOST"),
    user=os.getenv("DATABASE_USER"),
    password=os.getenv("DATABASE_PASSWORD"),
    port=os.getenv("DATABASE_PORT")
)
conn.autocommit = True

def get_cursor():
    return conn.cursor()

def run_query(sql, params=None):
    cur = get_cursor()
    cur.execute(sql, params)
    return cur

SEASON_SQL = """
    CASE
        WHEN EXTRACT(MONTH FROM o.order_datetime) IN (12,1,2) THEN 'Зима'
        WHEN EXTRACT(MONTH FROM o.order_datetime) IN (3,4,5)  THEN 'Весна'
        WHEN EXTRACT(MONTH FROM o.order_datetime) IN (6,7,8)  THEN 'Лето'
        ELSE 'Осень'
    END
"""

SEASON_ORDER = {'Весна': 1, 'Лето': 2, 'Осень': 3, 'Зима': 4}

class Task1Frame(Frame):
    def __init__(self, master):
        super().__init__(master)
        Label(self, text="Задание 1: Выручка по сезонам и моделям автомобилей",
              font=("Courier New", 12, "bold")).pack(pady=6)

        pf = Frame(self)
        pf.pack(pady=4)
        Label(pf, text="Параметр — статус заказа (arg1):").grid(row=0, column=0, padx=4)
        self.status_var = StringVar(value="Выполнен")
        cb = ttk.Combobox(pf, textvariable=self.status_var, width=14,
                          values=["Выполнен", "Отменён", "В пути", ""])
        cb.grid(row=0, column=1, padx=4)
        Label(pf, text="(пусто = все статусы)").grid(row=0, column=2, padx=4)

        ttk.Button(self, text="Сформировать отчёт", command=self.build).pack(pady=4)
        ttk.Button(self, text="Скопировать в буфер обмена", command=self.copy_to_clipboard).pack(pady=4)

        self.text = Text(self, font=("Courier New", 10), wrap="none",
                         bg="#1e1e1e", fg="#d4d4d4")
        sx = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        sy = ttk.Scrollbar(self, orient="vertical",   command=self.text.yview)
        self.text.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self.text.pack(fill="both", expand=True)
    def copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.text.get("1.0", "end").rstrip())
        messagebox.showinfo("Скопировано", "Текст отчёта скопирован в буфер обмена.")
    def build(self):
        arg1 = self.status_var.get().strip() or None

        sql = f"""
            SELECT
                {SEASON_SQL}                        AS season,
                c.model                             AS car_model,
                SUM(o.cost)::NUMERIC(10,2)          AS total_revenue,
                COUNT(*)::BIGINT                    AS order_count,
                AVG(o.cost)::NUMERIC(10,2)          AS avg_cost
            FROM orderr o
            JOIN car c ON c.license_plate = o.license_plate
            WHERE (%s IS NULL OR o.status = %s)
            GROUP BY season, c.model
            ORDER BY
                CASE {SEASON_SQL}
                    WHEN 'Весна' THEN 1 WHEN 'Лето' THEN 2
                    WHEN 'Осень' THEN 3 ELSE 4
                END,
                total_revenue DESC
        """
        rows = run_query(sql, (arg1, arg1)).fetchall()

        # Группировка по сезону
        groups = {}
        for season, model, rev, cnt, avg in rows:
            groups.setdefault(season, []).append((model, rev, cnt, avg))

        param_str = f'"{arg1}"' if arg1 else "все статусы"
        title = f"ОТЧЁТ: Выручка по сезонам и моделям автомобилей  |  Статус: {param_str}"
        w_no, w_model, w_rev, w_cnt, w_avg = 4, 22, 14, 8, 12
        sep  = "+" + "-"*(w_no+2) + "+" + "-"*(w_model+2) + "+" + \
               "-"*(w_rev+2) + "+" + "-"*(w_cnt+2) + "+" + "-"*(w_avg+2) + "+"
        sep2 = sep.replace("-", "=")

        def row_line(no, model, rev, cnt, avg):
            return (f"| {str(no).ljust(w_no)} | {model.ljust(w_model)} | "
                    f"{str(rev).rjust(w_rev)} | {str(cnt).rjust(w_cnt)} | "
                    f"{str(avg).rjust(w_avg)} |")

        lines = []
        lines.append(title)
        lines.append("=" * len(title))
        lines.append(sep2)
        lines.append(row_line("№", "Модель", "Выручка, руб.", "Заказов", "Ср. чек, руб."))
        lines.append(sep2)

        grand_total = 0
        for season, items in groups.items():
            season_total = sum(r for _, r, _, _ in items)
            grand_total += season_total
            # Шапка группы — сезон + итог по сезону
            lines.append(f"| {'':>{w_no}} | {f'[{season}]  Итого: {season_total:.2f} руб.'.ljust(w_model + w_rev + w_cnt + w_avg + 9)} |")
            lines.append(sep)
            for i, (model, rev, cnt, avg) in enumerate(items, 1):
                lines.append(row_line(i, model, f"{rev:.2f}", cnt, f"{avg:.2f}"))
            lines.append(sep)

        lines.append(f"| {'ВСЕГО':>{w_no}} | {'':>{w_model}} | {f'{grand_total:.2f}'.rjust(w_rev)} | {'':>{w_cnt}} | {'':>{w_avg}} |")
        lines.append(sep2)

        self.text.delete("1.0", "end")
        self.text.insert("end", "\n".join(lines))

class Task2Frame(Frame):
    def __init__(self, master):
        super().__init__(master)
        Label(self, text="Задание 2: Сводная таблица — пробег по водителям и сезонам",
              font=("Courier New", 12, "bold")).pack(pady=6)

        pf = Frame(self)
        pf.pack(pady=4)
        Label(pf, text="Параметр — статус заказа (arg1):").grid(row=0, column=0, padx=4)
        self.status_var = StringVar(value="Выполнен")
        ttk.Combobox(pf, textvariable=self.status_var, width=14,
                     values=["Выполнен", "Отменён", "В пути", ""]).grid(row=0, column=1, padx=4)
        Label(pf, text="(пусто = все)").grid(row=0, column=2)

        ttk.Button(self, text="Сформировать сводную таблицу", command=self.build).pack(pady=4)
        ttk.Button(self, text="Скопировать в буфер обмена", command=self.copy_to_clipboard).pack(pady=4)
        self.text = Text(self, font=("Courier New", 10), wrap="none",
                         bg="#1e1e1e", fg="#d4d4d4")
        sx = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        sy = ttk.Scrollbar(self, orient="vertical",   command=self.text.yview)
        self.text.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self.text.pack(fill="both", expand=True)
    def copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.text.get("1.0", "end").rstrip())
        messagebox.showinfo("Скопировано", "Текст сводной таблицы скопирован в буфер обмена.")
    def build(self):
        arg1 = self.status_var.get().strip() or None
        sql = f"""
            SELECT
                CASE {SEASON_SQL}
                    WHEN 'Весна' THEN 1 WHEN 'Лето' THEN 2
                    WHEN 'Осень' THEN 3 ELSE 4
                END                                     AS x,
                {SEASON_SQL}                            AS xname,
                o.employee_id                           AS y,
                e.last_name                             AS yname,
                r.mileage_km                            AS f,
                o.status                                AS param1
            FROM orderr o
            JOIN employee e ON e.employee_id = o.employee_id
            JOIN route    r ON r.order_id    = o.order_id
            WHERE (%s IS NULL OR o.status = %s)
            ORDER BY x, yname
        """
        rows = run_query(sql, (arg1, arg1)).fetchall()

        xname_list, yname_list = [], []
        xmap, ymap = {}, {}
        for x, xn, y, yn, f, p1 in rows:
            if xn not in xmap:
                xmap[xn] = len(xname_list)
                xname_list.append(xn)
            if yn not in ymap:
                ymap[yn] = len(yname_list)
                yname_list.append(yn)

        M, N = len(xname_list), len(yname_list)
        T  = [[0.0]*N for _ in range(M)]
        nT = [[0]*N   for _ in range(M)]

        for x, xn, y, yn, f, p1 in rows:
            i, j = xmap[xn], ymap[yn]
            T[i][j]  += float(f)
            nT[i][j] += 1

        sorted_y = sorted(range(N), key=lambda j: yname_list[j])
        yname_sorted = [yname_list[j] for j in sorted_y]
        T_sorted  = [[T[i][j]  for j in sorted_y] for i in range(M)]
        nT_sorted = [[nT[i][j] for j in sorted_y] for i in range(M)]

        param_str = f'"{arg1}"' if arg1 else "все статусы"
        title = f"СВОДНАЯ ТАБЛИЦА: Средний пробег (км) по сезонам и водителям  |  Статус: {param_str}"

        WX = 8   # ширина колонки сезон
        WN = 4   # ширина № строки
        WC = 7   # ширина ячейки с данными
        WIT = 8  # ширина Итого

        def cell(val, n):
            if n == 0:
                return "-".center(WC)
            return f"{val/n:.1f}".center(WC)

        def hdr_sep():
            parts = ["-"*(WN+2), "-"*(WX+2)]
            for _ in yname_sorted:
                parts.append("-"*(WC+2))
            parts.append("-"*(WIT+2))
            return "+" + "+".join(parts) + "+"

        lines = [title, "="*len(title)]

        lines.append(hdr_sep().replace("-","="))
        hdr = f"| {'№'.center(WN)} | {'Сезон'.center(WX)} |"
        for yn in yname_sorted:
            hdr += f" {yn[:WC].center(WC)} |"
        hdr += f" {'Итого'.center(WIT)} |"
        lines.append(hdr)
        lines.append(hdr_sep().replace("-","="))

        for i, xn in enumerate(xname_list):
            row_sum = sum(T_sorted[i])
            row_n   = sum(nT_sorted[i])
            row_avg = f"{row_sum/row_n:.1f}" if row_n else "-"
            line = f"| {str(i+1).center(WN)} | {xn.center(WX)} |"
            for j in range(len(yname_sorted)):
                line += f" {cell(T_sorted[i][j], nT_sorted[i][j])} |"
            line += f" {row_avg.center(WIT)} |"
            lines.append(line)
            lines.append(hdr_sep())

        all_line = f"| {''.center(WN)} | {'Всего'.center(WX)} |"
        grand_sum, grand_n = 0, 0
        for j in range(len(yname_sorted)):
            cs = sum(T_sorted[i][j]  for i in range(M))
            cn = sum(nT_sorted[i][j] for i in range(M))
            grand_sum += cs
            grand_n   += cn
            all_line  += f" {cell(cs, cn)} |"
        grand_avg = f"{grand_sum/grand_n:.1f}" if grand_n else "-"
        all_line += f" {grand_avg.center(WIT)} |"
        lines.append(all_line)
        lines.append(hdr_sep().replace("-","="))

        self.text.delete("1.0", "end")
        self.text.insert("end", "\n".join(lines))


class Task3Frame(Frame):
    def __init__(self, master):
        super().__init__(master)
        Label(self, text="Задание 3: График f1(t) и f2(t) по месяцам",
              font=("Courier New", 12, "bold")).pack(pady=6)

        pf = Frame(self)
        pf.pack(pady=4)
        Label(pf, text="T1 (YYYY-MM):").grid(row=0, column=0, padx=4)
        self.t1_var = StringVar(value="")
        Entry(pf, textvariable=self.t1_var, width=10).grid(row=0, column=1, padx=4)
        Label(pf, text="T2 (YYYY-MM):").grid(row=0, column=2, padx=4)
        self.t2_var = StringVar(value="")
        Entry(pf, textvariable=self.t2_var, width=10).grid(row=0, column=3, padx=4)
        Label(pf, text="(пусто = весь диапазон)").grid(row=0, column=4, padx=4)

        ttk.Button(self, text="Построить график", command=self.build).pack(pady=4)
        self.canvas_frame = Frame(self)
        self.canvas_frame.pack(fill="both", expand=True)

    def build(self):
        t1 = self.t1_var.get().strip() or None
        t2 = self.t2_var.get().strip() or None

        sql = """
            SELECT
                TO_CHAR(DATE_TRUNC('month', o.order_datetime), 'YYYY-MM') AS month,
                SUM(o.cost)::NUMERIC(10,2)                                AS f1_revenue,
                COUNT(*)::INT                                              AS f2_orders
            FROM orderr o
            WHERE o.status = 'Выполнен'
              AND (%s IS NULL OR DATE_TRUNC('month', o.order_datetime) >= %s::DATE)
              AND (%s IS NULL OR DATE_TRUNC('month', o.order_datetime) <= %s::DATE)
            GROUP BY DATE_TRUNC('month', o.order_datetime)
            ORDER BY DATE_TRUNC('month', o.order_datetime)
        """
        t1_val = (t1 + "-01") if t1 else None
        t2_val = (t2 + "-01") if t2 else None
        rows = run_query(sql, (t1_val, t1_val, t2_val, t2_val)).fetchall()

        if not rows:
            messagebox.showinfo("Нет данных", "Нет данных для выбранного диапазона.")
            return

        months = [r[0] for r in rows]
        f1 = [float(r[1]) for r in rows]
        f2 = [r[2] for r in rows]
        xs = range(len(months))

        for w in self.canvas_frame.winfo_children():
            w.destroy()

        fig, ax1 = plt.subplots(figsize=(10, 4))
        ax2 = ax1.twinx()

        ax1.plot(xs, f1, color="steelblue", marker="o", linewidth=2, label="f1 — Выручка, руб.")
        ax2.bar(xs, f2, color="lightcoral", alpha=0.5, label="f2 — Кол-во заказов")

        ax1.set_xticks(list(xs))
        ax1.set_xticklabels(months, rotation=45, ha="right", fontsize=8)
        ax1.set_ylabel("Выручка, руб.", color="steelblue")
        ax2.set_ylabel("Количество заказов", color="lightcoral")
        ax1.set_title(f"Выручка и количество заказов по месяцам  |  {t1 or 'начало'} — {t2 or 'конец'}")

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)


class Task4Frame(Frame):
    def __init__(self, master):
        super().__init__(master)
        Label(self, text="Задание 4: Круговая диаграмма — выручка по моделям автомобилей",
              font=("Courier New", 12, "bold")).pack(pady=6)

        pf = Frame(self)
        pf.pack(pady=4)
        Label(pf, text="Параметр — сезон (arg1 = y):").grid(row=0, column=0, padx=4)
        self.season_var = StringVar(value="")
        ttk.Combobox(pf, textvariable=self.season_var, width=10,
                     values=["Весна", "Лето", "Осень", "Зима", ""]).grid(row=0, column=1, padx=4)
        Label(pf, text="(пусто = все сезоны)").grid(row=0, column=2, padx=4)

        ttk.Button(self, text="Построить диаграмму", command=self.build).pack(pady=4)
        self.canvas_frame = Frame(self)
        self.canvas_frame.pack(fill="both", expand=True)

    def build(self):
        arg_season = self.season_var.get().strip() or None

        sql = f"""
            SELECT
                c.model                        AS car_model,
                SUM(o.cost)::NUMERIC(10,2)     AS total_revenue
            FROM orderr o
            JOIN car c ON c.license_plate = o.license_plate
            WHERE o.status = 'Выполнен'
              AND (%s IS NULL OR ({SEASON_SQL}) = %s)
            GROUP BY c.model
            ORDER BY total_revenue DESC
        """
        rows = run_query(sql, (arg_season, arg_season)).fetchall()

        if not rows:
            messagebox.showinfo("Нет данных", "Нет данных для выбранного сезона.")
            return

        labels = [r[0] for r in rows]
        values = [float(r[1]) for r in rows]
        total  = sum(values)

        for w in self.canvas_frame.winfo_children():
            w.destroy()

        fig, ax = plt.subplots(figsize=(7, 5))
        wedges, texts, autotexts = ax.pie(
            values, labels=None,
            autopct=lambda p: f"{p:.1f}%\n({p*total/100:,.0f} р.)",
            startangle=140,
            pctdistance=0.75,
            colors=plt.cm.Set3.colors
        )
        for at in autotexts:
            at.set_fontsize(8)

        season_str = arg_season if arg_season else "все сезоны"
        ax.set_title(f"Доля выручки по моделям автомобилей\nСезон: {season_str}")
        ax.legend(wedges, [f"{l} — {v:,.0f} р." for l, v in zip(labels, values)],
                  loc="lower left", fontsize=8)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)


def main():
    root = Tk()
    root.title("TaxiManager — ЛР8 | Подпорин Н.Ю.")
    root.geometry("1100x700")
    root.configure(bg="#f0f0f0")

    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=8, pady=8)

    t1 = Task1Frame(nb)
    t2 = Task2Frame(nb)
    t3 = Task3Frame(nb)
    t4 = Task4Frame(nb)

    nb.add(t1, text="  Задание 1: Текстовый отчёт  ")
    nb.add(t2, text="  Задание 2: Сводная таблица  ")
    nb.add(t3, text="  Задание 3: График  ")
    nb.add(t4, text="  Задание 4: Диаграмма  ")

    root.mainloop()
    conn.close()


if __name__ == "__main__":
    main()
