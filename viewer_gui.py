import tkinter as tk
from tkinter import ttk
from typing import Callable


def run_viewer(list_boards: Callable[[], list]):
    root = tk.Toplevel()
    root.title("LED Boards Viewer (Read-only)")
    root.geometry("1000x500")
    try:
        import os
        ico_path = os.path.join(os.path.dirname(__file__), 'assets', 'app.ico')
        if os.path.exists(ico_path):
            root.iconbitmap(ico_path)
    except Exception:
        pass

    # Filters toolbar
    filter_bar = ttk.LabelFrame(root, text="Filters")
    filter_bar.pack(fill="x", padx=10, pady=(10, 4))
    ttk.Label(filter_bar, text="Site Name:").grid(row=0, column=0, padx=6, pady=4, sticky="w")
    cmb_site = ttk.Combobox(filter_bar, values=["All"], state="readonly", width=22)
    cmb_site.set("All")
    cmb_site.grid(row=0, column=1, padx=6, pady=4, sticky="w")
    ttk.Label(filter_bar, text="Size:").grid(row=0, column=2, padx=6, pady=4, sticky="w")
    cmb_size = ttk.Combobox(filter_bar, values=["All"], state="readonly", width=14)
    cmb_size.set("All")
    cmb_size.grid(row=0, column=3, padx=6, pady=4, sticky="w")
    ttk.Label(filter_bar, text="Done by:").grid(row=0, column=4, padx=6, pady=4, sticky="w")
    cmb_user = ttk.Combobox(filter_bar, values=["All"], state="readonly", width=18)
    cmb_user.set("All")
    cmb_user.grid(row=0, column=5, padx=6, pady=4, sticky="w")
    ttk.Label(filter_bar, text="Urgency:").grid(row=0, column=6, padx=6, pady=4, sticky="w")
    cmb_urg = ttk.Combobox(filter_bar, values=["All", "Yes", "No"], state="readonly", width=8)
    cmb_urg.set("All")
    cmb_urg.grid(row=0, column=7, padx=6, pady=4, sticky="w")
    ttk.Label(filter_bar, text="Month(s) by Date Request:").grid(row=1, column=0, padx=6, pady=4, sticky="w")
    months_frame = ttk.Frame(filter_bar)
    months_frame.grid(row=1, column=1, columnspan=3, padx=6, pady=4, sticky="w")
    month_names = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]
    month_vars = {m: tk.BooleanVar(value=False) for m in month_names}
    # Lay out checkboxes in two rows for clarity
    for idx, m in enumerate(month_names):
        r = 0 if idx < 6 else 1
        c = idx if idx < 6 else idx - 6
        ttk.Checkbutton(months_frame, text=m, variable=month_vars[m]).grid(row=r, column=c, padx=4, pady=2, sticky="w")
    def select_all_months():
        for v in month_vars.values():
            v.set(True)
    def clear_all_months():
        for v in month_vars.values():
            v.set(False)
    ttk.Button(months_frame, text="All", command=select_all_months).grid(row=2, column=0, padx=4, pady=2, sticky="w")
    ttk.Button(months_frame, text="None", command=clear_all_months).grid(row=2, column=1, padx=4, pady=2, sticky="w")

    ttk.Label(filter_bar, text="Sort by:").grid(row=1, column=4, padx=6, pady=4, sticky="w")
    cmb_sort = ttk.Combobox(filter_bar, state="readonly", width=28, values=[
        "None",
        "Date Request: Newest first",
        "Date Request: Oldest first",
        "Module Number: Ascending",
        "Module Number: Descending",
    ])
    cmb_sort.set("None")
    cmb_sort.grid(row=1, column=5, columnspan=2, padx=6, pady=4, sticky="w")

    def clear_filters():
        cmb_site.set("All")
        cmb_size.set("All")
        cmb_user.set("All")
        cmb_urg.set("All")
        cmb_sort.set("None")
        clear_all_months()
        refresh()
    ttk.Button(filter_bar, text="Apply", command=lambda: refresh()).grid(row=0, column=8, padx=6, pady=4)
    ttk.Button(filter_bar, text="Clear", command=clear_filters).grid(row=0, column=9, padx=6, pady=4)

    # Table of boards (read-only)
    frame = ttk.Frame(root)
    frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))

    columns = (
        "ID", "Site Name", "IC", "DC", "Size", "Module Number", "Pixel", "Board Code", "Running No",
        "Date Request", "DO Date", "Date Repair", "Before Photo", "After Photo", "Urgency", "Added by"
    )
    tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
    # Header click sorting still available
    sort_state = {"col": None, "reverse": False}

    def on_sort(col):
        if sort_state["col"] == col:
            sort_state["reverse"] = not sort_state["reverse"]
        else:
            sort_state["col"] = col
            sort_state["reverse"] = False
        refresh()

    for col in columns:
        tree.heading(col, text=col, command=lambda c=col: on_sort(c))
        width = 120
        if col in {"ID", "IC", "DC"}: width = 80
        if col in {"Size", "Pixel", "Running No"}: width = 90
        if col in {"Urgency"}: width = 80
        tree.column(col, width=width, anchor="w")

    yscroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    xscroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
    tree.pack(fill="both", expand=True)
    yscroll.pack(side="right", fill="y")
    xscroll.pack(fill="x")

    def yn(v: bool) -> str:
        return "✔" if bool(v) else "✘"

    def refresh():
        for i in tree.get_children():
            tree.delete(i)
        boards = list_boards()
        # Update selectable values from database
        users = sorted({b.get("created_by") or "-" for b in boards if b.get("created_by")})
        cmb_user.configure(values=["All"] + users)
        sites = sorted({b.get("name") or "-" for b in boards if b.get("name")})
        sizes = sorted({b.get("size") or "-" for b in boards if b.get("size")})
        cmb_site.configure(values=["All"] + sites)
        cmb_size.configure(values=["All"] + sizes)

        # Apply filters
        site_choice = cmb_site.get()
        size_choice = cmb_size.get()
        user_q = cmb_user.get()
        urg_q = cmb_urg.get()
        # Month selections (by Date Request)
        sel_months = [m for m in month_names if month_vars[m].get()]
        month_map = {
            "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
            "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
        }
        def match(b):
            if site_choice and site_choice != "All" and (b.get("name") or "-") != site_choice:
                return False
            if size_choice and size_choice != "All" and (b.get("size") or "-") != size_choice:
                return False
            if user_q and user_q != "All" and (b.get("created_by") or "-") != user_q:
                return False
            if urg_q != "All":
                want = True if urg_q == "Yes" else False
                if bool(b.get("urgency", False)) != want:
                    return False
            if sel_months:
                dr = str(b.get("date_request") or "")
                try:
                    parts = dr.split("-")
                    if len(parts) >= 2:
                        month = int(parts[1])
                        if month not in {month_map[m] for m in sel_months}:
                            return False
                    else:
                        return False
                except Exception:
                    return False
            return True
        boards = [b for b in boards if match(b)]

        # Sorting
        col = sort_state["col"]
        rev = sort_state["reverse"]
        sort_choice = cmb_sort.get()
        def key_for(b):
            if col == "ID":
                s = str(b.get("board_id") or "")
                return (0, int(s)) if s.isdigit() else (1, s)
            mapping = {
                "Site Name": "name",
                "IC": "ic",
                "DC": "dc",
                "Size": "size",
                "Module Number": "module_number",
                "Pixel": "pixel",
                "Board Code": "board_code",
                "Running No": "running_no",
                "Date Request": "date_request",
                "DO Date": "do_date",
                "Date Repair": "date_repair",
                "Before Photo": "before_photo",
                "After Photo": "after_photo",
                "Added by": "created_by",
                "Urgency": "urgency",
            }
            if col in {"No issue", "Total loss"}:
                iss = b.get("issues") or {}
                key = "no_issue" if col == "No issue" else "total_loss"
                return bool(iss.get(key, False))
            field = mapping.get(col)
            if not field:
                return ""
            val = b.get(field)
            if field == "urgency":
                return 1 if bool(val) else 0
            return str(val or "").lower()
        if sort_choice and sort_choice != "None":
            if sort_choice.startswith("Date Request"):
                def dr_key(x):
                    return str(x.get("date_request") or "")
                boards.sort(key=dr_key, reverse=("Newest" in sort_choice))
            elif sort_choice.startswith("Module Number"):
                def mn_key(x):
                    v = str(x.get("module_number") or "").strip()
                    return (0, int(v)) if v.isdigit() else (1, v.lower())
                boards.sort(key=mn_key, reverse=("Desc" in sort_choice))
        elif col:
            boards.sort(key=key_for, reverse=rev)

        for b in boards:
            tree.insert("", "end", values=(
                b.get("board_id"),
                b.get("name"),
                b.get("ic"),
                b.get("dc"),
                b.get("size"),
                b.get("module_number") or "-",
                b.get("pixel") or "-",
                b.get("board_code") or "-",
                b.get("running_no") or "-",
                b.get("date_request") or "-",
                b.get("do_date") or "-",
                b.get("date_repair") or "-",
                b.get("before_photo") or "-",
                b.get("after_photo") or "-",
                yn(b.get("urgency", False)),
                b.get("created_by") or "-",
            ))

    # Toolbar
    toolbar = ttk.Frame(root)
    toolbar.pack(fill="x", padx=10, pady=6)
    ttk.Button(toolbar, text="Refresh", command=refresh).pack(side="left")
    ttk.Button(toolbar, text="Close", command=root.destroy).pack(side="right")

    refresh()
    root.grab_set()
    root.focus_set()
    root.transient()
    # Let caller manage mainloop; this is a top-level window