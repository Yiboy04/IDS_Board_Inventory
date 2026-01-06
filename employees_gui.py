import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Dict


def add_employees_tab(
    notebook: ttk.Notebook,
    *,
    list_employees: Callable[[], List[Dict]],
    add_or_update_employee: Callable[[str, str], Dict],
    delete_employee: Callable[[str], bool],
):
    frm_root = ttk.Frame(notebook)
    notebook.add(frm_root, text="Employees (Admin)")

    frm_form = ttk.LabelFrame(frm_root, text="Employee Details")
    frm_form.pack(fill="x", padx=10, pady=10)

    ttk.Label(frm_form, text="Username:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
    ent_user = ttk.Entry(frm_form, width=30)
    ent_user.grid(row=0, column=1, sticky="w", padx=6, pady=4)

    ttk.Label(frm_form, text="Password:").grid(row=1, column=0, sticky="w", padx=6, pady=4)
    ent_pass = ttk.Entry(frm_form, width=30, show="*")
    ent_pass.grid(row=1, column=1, sticky="w", padx=6, pady=4)

    frm_btn = ttk.Frame(frm_root)
    frm_btn.pack(fill="x", padx=10, pady=6)

    frm_table = ttk.Frame(frm_root)
    frm_table.pack(fill="both", expand=True, padx=10, pady=10)

    tree = ttk.Treeview(frm_table, columns=("Username"), show="headings")
    tree.heading("Username", text="Username")
    tree.column("Username", width=200)
    tree.pack(fill="both", expand=True)

    def refresh_emps():
        for i in tree.get_children():
            tree.delete(i)
        for e in list_employees():
            u = e.get("username")
            if u == "admin":
                continue
            tree.insert("", "end", values=(u,))

    def on_save_emp():
        u = ent_user.get().strip()
        p = ent_pass.get().strip()
        if not u or not p:
            messagebox.showwarning("Input", "Username and password are required")
            return
        try:
            add_or_update_employee(u, p)
            refresh_emps()
            messagebox.showinfo("Saved", "Employee saved.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_delete_emp():
        item = tree.focus()
        if not item:
            messagebox.showwarning("Select", "Please select an employee.")
            return
        u = tree.item(item, "values")[0]
        if delete_employee(u):
            refresh_emps()
            messagebox.showinfo("Deleted", f"Deleted employee '{u}'.")
        else:
            messagebox.showwarning("Not found", "Employee not found or protected.")

    def on_select_fill(event=None):
        item = tree.focus()
        if not item:
            return
        u = tree.item(item, "values")[0]
        ent_user.delete(0, tk.END)
        ent_user.insert(0, u)
        ent_pass.delete(0, tk.END)
        # Do not show existing password

    btn_save = ttk.Button(frm_btn, text="Add / Update", command=on_save_emp)
    btn_save.pack(side="left", padx=4)

    btn_del = ttk.Button(frm_btn, text="Delete Selected", command=on_delete_emp)
    btn_del.pack(side="left", padx=4)

    btn_ref = ttk.Button(frm_btn, text="Refresh", command=refresh_emps)
    btn_ref.pack(side="left", padx=4)

    tree.bind("<<TreeviewSelect>>", on_select_fill)
    refresh_emps()
