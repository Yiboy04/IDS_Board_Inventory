import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from typing import Callable
import datetime
import calendar

# run_gui accepts callables so we avoid importing Main and circular deps.
# Required functions passed in:
# - list_boards, add_board, delete_board, find_board_by_id
# - find_employee, add_or_update_employee, delete_employee

def run_gui(
    list_boards: Callable[[], list],
    add_board: Callable[[str, str, str, str, str, str | None, str | None, str | None, str | None, bool, dict | None, str | None], dict],
    delete_board: Callable[[str], bool],
    find_board_by_id: Callable[[str], dict | None],
    find_employee: Callable[[str], dict | None],
    list_employees: Callable[[], list],
    add_or_update_employee: Callable[[str, str], dict],
    delete_employee: Callable[[str], bool],
):
    root = tk.Tk()
    root.title("LED Board Manager")
    root.geometry("900x520")
    # Apply window icon if assets/app.ico exists
    try:
        import os
        ico_path = os.path.join(os.path.dirname(__file__), 'assets', 'app.ico')
        if os.path.exists(ico_path):
            root.iconbitmap(ico_path)
    except Exception:
        pass

    current_user = None
    current_role = None  # 'admin' or 'employee'

    # Data dir helper (mirrors Main._get_data_dir logic)
    def _get_data_dir() -> str:
        try:
            cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
            if os.path.exists(cfg_path):
                import json
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    dd = cfg.get("data_dir")
                    if isinstance(dd, str) and dd.strip():
                        return dd
        except Exception:
            pass
        return os.path.join(os.path.dirname(__file__), "data")

    def show_boards_tab(notebook: ttk.Notebook):
        frm_root = ttk.Frame(notebook)
        notebook.add(frm_root, text="Boards")

        frm_form = ttk.LabelFrame(frm_root, text="Board Details")
        frm_form.pack(fill="x", padx=10, pady=10)
        # Hide the static form; use pop-up dialogs for add/edit
        try:
            frm_form.pack_forget()
        except Exception:
            pass

        # Simple tooltip helper
        class ToolTip:
            def __init__(self, widget, text: str):
                self.widget = widget
                self.text = text
                self.tip = None
                widget.bind("<Enter>", self.show)
                widget.bind("<Leave>", self.hide)
            def show(self, _event=None):
                if self.tip:
                    return
                x = self.widget.winfo_rootx() + 15
                y = self.widget.winfo_rooty() + 20
                self.tip = tk.Toplevel(self.widget)
                self.tip.wm_overrideredirect(True)
                self.tip.wm_geometry(f"+{x}+{y}")
                lbl = ttk.Label(self.tip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1, padding=(6, 4))
                lbl.pack()
            def hide(self, _event=None):
                if self.tip:
                    self.tip.destroy()
                    self.tip = None

        # Date picker dialog
        def open_date_picker(set_value_cb, initial: str | None = None):
            today = datetime.date.today()
            try:
                if initial:
                    y, m, d = [int(x) for x in initial.split("-")]
                    current = datetime.date(y, m, d)
                else:
                    current = today
            except Exception:
                current = today

            win = tk.Toplevel(frm_root)
            win.title("Select Date")
            try:
                import os
                ico_path = os.path.join(os.path.dirname(__file__), 'assets', 'app.ico')
                if os.path.exists(ico_path):
                    win.iconbitmap(ico_path)
            except Exception:
                pass
            hdr = ttk.Frame(win)
            hdr.pack(fill="x", padx=8, pady=6)
            body = ttk.Frame(win)
            body.pack(padx=8, pady=6)

            sel = {"date": current}
            # Single month label; update its text on re-render to avoid duplicates
            hdr_label = ttk.Label(hdr, text="", font=("Segoe UI", 10, "bold"))
            hdr_label.pack(side="left", padx=6)

            def render():
                for c in body.winfo_children():
                    c.destroy()
                year = sel["date"].year
                month = sel["date"].month
                hdr_label.config(text=f"{calendar.month_name[month]} {year}")
                # Days of week header
                row0 = ttk.Frame(body)
                row0.pack()
                for wd in ["Mo","Tu","We","Th","Fr","Sa","Su"]:
                    ttk.Label(row0, text=wd, width=3, anchor="center").pack(side="left", padx=2, pady=2)
                # Dates grid
                for week in calendar.monthcalendar(year, month):
                    row = ttk.Frame(body)
                    row.pack()
                    for d in week:
                        if d == 0:
                            ttk.Label(row, text=" ", width=3).pack(side="left", padx=2, pady=2)
                        else:
                            def mkcmd(dd=d):
                                def _set():
                                    set_value_cb(f"{year:04d}-{month:02d}-{dd:02d}")
                                    win.destroy()
                                return _set
                            btn = ttk.Button(row, text=f"{d:02d}", width=3, command=mkcmd())
                            btn.pack(side="left", padx=2, pady=2)

            def prev_month():
                d = sel["date"]
                first = (d.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
                sel["date"] = first
                render()

            def next_month():
                d = sel["date"]
                days = calendar.monthrange(d.year, d.month)[1]
                first_next = (d.replace(day=days) + datetime.timedelta(days=1)).replace(day=1)
                sel["date"] = first_next
                render()

            ttk.Button(hdr, text="<", width=3, command=prev_month).pack(side="right")
            ttk.Button(hdr, text=">", width=3, command=next_month).pack(side="right")
            render()

        # Left and right columns for inputs
        # Left: labels and tooltips; keep keys stable even if labels change
        left_fields = [
            {"label": "Board ID", "key": "board_id", "tip": "Primary key (auto-assigned)"},
            {"label": "Site Name", "key": "name", "tip": "Location/site name where the board is installed"},
            {"label": "IC", "key": "ic", "tip": "Controller IC type (e.g., SM1627P)"},
            {"label": "DC", "key": "dc", "tip": "Logic IC / driver (e.g., 74HC368)"},
            {"label": "Size", "key": "size", "tip": "Module size or dimensions (e.g., 64x64)"},
            {"label": "Module Number", "key": "module_number", "tip": "Module/unit number for site tracking"},
        ]
        entries = {}
        # Left column entries with inline '?' tooltip next to entry
        for i, f in enumerate(left_fields):
            ttk.Label(frm_form, text=f["label"]+":").grid(row=i, column=0, sticky="w", padx=6, pady=4)
            container = ttk.Frame(frm_form)
            container.grid(row=i, column=1, sticky="w", padx=6, pady=4)
            ent = ttk.Entry(container, width=36)
            ent.pack(side="left")
            q = ttk.Label(container, text="?", width=2, foreground="#555")
            q.pack(side="left", padx=4)
            ToolTip(q, f.get("tip") or "")
            entries[f["key"]] = ent
            # Board ID should be read-only
            if f["key"] == "board_id":
                try:
                    ent.config(state="readonly")
                except Exception:
                    pass
        # Helper to compute next auto-increment Board ID (string)
        def compute_next_board_id() -> str:
            max_id = 0
            try:
                for b in list_boards():
                    bid = str(b.get("board_id", "")).strip()
                    if bid.isdigit():
                        max_id = max(max_id, int(bid))
            except Exception:
                pass
            return str(max_id + 1)

        def set_entry_value(ent: ttk.Entry, value: str):
            try:
                st = ent.cget("state")
                ent.config(state="normal")
                ent.delete(0, tk.END)
                ent.insert(0, value)
                ent.config(state=st)
            except Exception:
                ent.delete(0, tk.END)
                ent.insert(0, value)

        # Right column entries created explicitly so we can add calendar buttons and tooltips
        right_row = 0
        def add_field(label, key, tooltip: str | None = None, is_date: bool = False, is_file: bool = False):
            nonlocal right_row
            ttk.Label(frm_form, text=label+":").grid(row=right_row, column=2, sticky="w", padx=6, pady=4)
            if is_date:
                container = ttk.Frame(frm_form)
                container.grid(row=right_row, column=3, sticky="w", padx=6, pady=4)
                ent = ttk.Entry(container, width=30)
                ent.pack(side="left")
                def setter(val, e=ent):
                    e.delete(0, tk.END)
                    e.insert(0, val)
                ttk.Button(container, text="📅", width=3, command=lambda e=ent: open_date_picker(lambda v: setter(v), ent.get() or None)).pack(side="left", padx=4)
            elif is_file:
                container = ttk.Frame(frm_form)
                container.grid(row=right_row, column=3, sticky="w", padx=6, pady=4)
                ent = ttk.Entry(container, width=30)
                ent.pack(side="left")
                def browse(e=ent):
                    path = filedialog.askopenfilename(title="Select Image", filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All files", "*.*")])
                    if path:
                        e.delete(0, tk.END)
                        e.insert(0, path)
                ttk.Button(container, text="Browse", command=browse).pack(side="left", padx=4)
            else:
                ent = ttk.Entry(frm_form, width=40)
                ent.grid(row=right_row, column=3, sticky="w", padx=6, pady=4)
            entries[key] = ent
            if tooltip:
                q = ttk.Label(frm_form, text="?", width=2, foreground="#555")
                q.grid(row=right_row, column=4, sticky="w")
                ToolTip(q, tooltip)
            right_row += 1

        # Pixel removed; merged conceptually with Size
        add_field("Board Code", "board_code", "Internal board code / part number")
        add_field("Running No", "running_no", "Running/serial number for tracking")
        add_field("Date Request", "date_request", "Date when repair/inspection was requested", is_date=True)
        add_field("DO Date", "do_date", "Delivery Order date", is_date=True)
        add_field("Date Repair", "date_repair", "Date when repair was completed", is_date=True)
        add_field("Before Photo", "before_photo", "Image before repair (png/jpg)", is_file=True)
        add_field("After Photo", "after_photo", "Image after repair (png/jpg)", is_file=True)

        # Urgency checkbox under right column
        urgency_var = tk.BooleanVar(value=False)
        urg_chk = ttk.Checkbutton(frm_form, text="Urgency", variable=urgency_var)
        urg_chk.grid(row=right_row, column=2, sticky="w", padx=6, pady=4)
        ToolTip(urg_chk, "Mark as urgent to prioritize")

        frm_btn = ttk.Frame(frm_root)
        frm_btn.pack(fill="x", padx=10, pady=6)

        # Quantity moved to Add dialog; toolbar remains clean

        frm_table = ttk.Frame(frm_root)
        frm_table.pack(fill="both", expand=True, padx=10, pady=10)

        # Hidden filter state and a button to open a pop-up dialog
        def unique_values(key):
            vals = sorted({(b.get(key) or "") for b in list_boards() if b.get(key)})
            return ["All"] + vals
        site_var = tk.StringVar(value="All")
        size_var = tk.StringVar(value="All")
        user_var = tk.StringVar(value="All")
        urg_var = tk.StringVar(value="All")
        sort_var = tk.StringVar(value="Date Request (Newest)")
        month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        month_vars = {m: tk.BooleanVar(value=False) for m in month_names}

        def open_filters_dialog():
            win = tk.Toplevel(frm_root)
            win.title("Filters & Sort")
            try:
                import os
                ico_path = os.path.join(os.path.dirname(__file__), 'assets', 'app.ico')
                if os.path.exists(ico_path):
                    win.iconbitmap(ico_path)
            except Exception:
                pass
            frm = ttk.Frame(win)
            frm.pack(fill="both", expand=True, padx=10, pady=10)
            ttk.Label(frm, text="Site:").grid(row=0, column=0, padx=6, pady=4, sticky="w")
            site_cb = ttk.Combobox(frm, width=20, textvariable=site_var, values=unique_values("name"), state="readonly")
            site_cb.grid(row=0, column=1, padx=6, pady=4, sticky="w")
            ttk.Label(frm, text="Size:").grid(row=0, column=2, padx=6, pady=4, sticky="w")
            size_cb = ttk.Combobox(frm, width=12, textvariable=size_var, values=unique_values("size"), state="readonly")
            size_cb.grid(row=0, column=3, padx=6, pady=4, sticky="w")
            ttk.Label(frm, text="Done by:").grid(row=0, column=4, padx=6, pady=4, sticky="w")
            user_cb = ttk.Combobox(frm, width=14, textvariable=user_var, values=unique_values("created_by"), state="readonly")
            user_cb.grid(row=0, column=5, padx=6, pady=4, sticky="w")
            ttk.Label(frm, text="Urgency:").grid(row=0, column=6, padx=6, pady=4, sticky="w")
            urg_cb = ttk.Combobox(frm, width=10, textvariable=urg_var, values=["All", "Yes", "No"], state="readonly")
            urg_cb.grid(row=0, column=7, padx=6, pady=4, sticky="w")
            ttk.Label(frm, text="Month(s) by Date Request:").grid(row=1, column=0, padx=6, pady=4, sticky="w")
            months_frame = ttk.Frame(frm)
            months_frame.grid(row=1, column=1, columnspan=3, padx=6, pady=4, sticky="w")
            for idx, m in enumerate(month_names):
                r = 0 if idx < 6 else 1
                c = idx if idx < 6 else idx-6
                ttk.Checkbutton(months_frame, text=m, variable=month_vars[m]).grid(row=r, column=c, padx=4, pady=2, sticky="w")
            def select_all_months():
                for v in month_vars.values(): v.set(True)
            def clear_all_months():
                for v in month_vars.values(): v.set(False)
            ttk.Button(months_frame, text="All", command=select_all_months).grid(row=2, column=0, padx=4, pady=2, sticky="w")
            ttk.Button(months_frame, text="None", command=clear_all_months).grid(row=2, column=1, padx=4, pady=2, sticky="w")
            ttk.Label(frm, text="Sort by:").grid(row=1, column=4, padx=6, pady=4, sticky="w")
            sort_cb = ttk.Combobox(frm, width=22, textvariable=sort_var, state="readonly",
                values=["Date Request (Newest)", "Date Request (Oldest)", "Module Number (Asc)", "Module Number (Desc)", "Running No (Asc)", "Running No (Desc)"])
            sort_cb.grid(row=1, column=5, padx=6, pady=4, sticky="w")
            def on_ok():
                refresh_tree()
                win.destroy()
            ttk.Button(frm, text="OK", command=on_ok).grid(row=2, column=5, padx=6, pady=8, sticky="e")
            ttk.Button(frm, text="Clear", command=lambda: [site_var.set("All"), size_var.set("All"), user_var.set("All"), urg_var.set("All"), sort_var.set("Date Request (Newest)"), clear_all_months(), refresh_tree()]).grid(row=2, column=4, padx=6, pady=8, sticky="e")

        ttk.Button(frm_btn, text="Filters...", command=open_filters_dialog).pack(side="left", padx=4)

        # Add selectable checkbox column
        selected_ids = set()
        columns = ("Select", "ID", "Site Name", "IC", "DC", "Size")
        tree = ttk.Treeview(frm_table, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            default_w = 120
            if col == "Select":
                default_w = 60
            elif col == "Site Name":
                default_w = 180
            tree.column(col, width=default_w)
        tree.pack(fill="both", expand=True)

        # Issue fields and state
        issue_fields = [
            "caterpillar",
            "lamp pixel drop",
            "lamp pixel problem",
            "kaki patah",
            "green/red/blue line",
            "box problem",
            "half/whole module blackout",
            "broken module",
            "broken connector",
            "broken power socket",
            "wiring",
            "broken frame",
        ]
        issue_vars = {k: tk.IntVar(value=0) for k in issue_fields}
        no_issue_var = tk.BooleanVar(value=False)
        total_loss_var = tk.BooleanVar(value=False)
        spin_widgets = {}

        def open_issues_dialog():
            win = tk.Toplevel(frm_root)
            win.title("Issues")
            try:
                import os
                ico_path = os.path.join(os.path.dirname(__file__), 'assets', 'app.ico')
                if os.path.exists(ico_path):
                    win.iconbitmap(ico_path)
            except Exception:
                pass
            container = ttk.Frame(win)
            container.pack(fill="both", expand=True, padx=10, pady=10)
            # Checkboxes row
            chk_frame = ttk.Frame(container)
            chk_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=6)
            def apply_no_issue_state():
                if no_issue_var.get():
                    for k in issue_fields:
                        issue_vars[k].set(0)
                        try:
                            spin_widgets[k]['state'] = 'disabled'
                        except Exception:
                            pass
                else:
                    for k in issue_fields:
                        try:
                            spin_widgets[k]['state'] = 'normal'
                        except Exception:
                            pass
            ttk.Checkbutton(chk_frame, text="No issue", variable=no_issue_var, command=apply_no_issue_state).pack(side="left", padx=6)
            ttk.Checkbutton(chk_frame, text="Total loss", variable=total_loss_var).pack(side="left", padx=6)

            # Issue controls start from row 1
            for idx, key in enumerate(issue_fields, start=1):
                ttk.Label(container, text=key+":").grid(row=idx, column=0, sticky="w", padx=6, pady=4)
                sp = tk.Spinbox(container, from_=0, to=999, width=8, textvariable=issue_vars[key])
                sp.grid(row=idx, column=1, sticky="w", padx=6, pady=4)
                spin_widgets[key] = sp
            ttk.Button(container, text="Close", command=win.destroy).grid(row=len(issue_fields)+2, column=0, padx=6, pady=10, sticky="w")
            apply_no_issue_state()

        def get_filtered_boards():
            data = list_boards()
            # Site
            s = site_var.get()
            if s and s != "All":
                data = [b for b in data if str(b.get("name")) == s]
            # Size
            sz = size_var.get()
            if sz and sz != "All":
                data = [b for b in data if str(b.get("size")) == sz]
            # Done by
            du = user_var.get()
            if du and du != "All":
                data = [b for b in data if str(b.get("created_by")) == du]
            # Urgency
            ug = urg_var.get()
            if ug == "Yes":
                data = [b for b in data if bool(b.get("urgency", False))]
            elif ug == "No":
                data = [b for b in data if not bool(b.get("urgency", False))]
            # Months by Date Request
            sel_months = [m for m in month_names if month_vars[m].get()]
            if sel_months:
                mindex = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
                def dm(b):
                    d = b.get("date_request")
                    if not d:
                        return None
                    try:
                        parts = str(d).split("-")
                        return int(parts[1])
                    except Exception:
                        return None
                sel_nums = {mindex[m] for m in sel_months}
                data = [b for b in data if dm(b) in sel_nums]
            # Sort
            sv = sort_var.get()
            def keydate(b):
                import datetime
                try:
                    return datetime.datetime.strptime(str(b.get("date_request")), "%Y-%m-%d")
                except Exception:
                    return datetime.datetime(1900,1,1)
            def keyint(b, k):
                try:
                    return int(str(b.get(k) or "0"))
                except Exception:
                    return 0
            if sv == "Date Request (Newest)":
                data.sort(key=keydate, reverse=True)
            elif sv == "Date Request (Oldest)":
                data.sort(key=keydate)
            elif sv == "Module Number (Asc)":
                data.sort(key=lambda b: keyint(b, "module_number"))
            elif sv == "Module Number (Desc)":
                data.sort(key=lambda b: keyint(b, "module_number"), reverse=True)
            elif sv == "Running No (Asc)":
                data.sort(key=lambda b: keyint(b, "running_no"))
            elif sv == "Running No (Desc)":
                data.sort(key=lambda b: keyint(b, "running_no"), reverse=True)
            return data

        def refresh_tree():
            for i in tree.get_children():
                tree.delete(i)
            for b in get_filtered_boards():
                bid = str(b.get("board_id"))
                chk = "☑" if bid in selected_ids else "☐"
                tree.insert("", "end", values=(
                    chk, bid, b.get("name"), b.get("ic"), b.get("dc"), b.get("size")
                ))


        # Clear form helper
        def clear_form():
            keys = [
                "board_id", "name", "ic", "dc", "size",
                "module_number", "board_code", "running_no",
                "date_request", "do_date", "date_repair"
            ]
            for key in keys:
                ent = entries.get(key)
                if not ent:
                    continue
                try:
                    st = ent.cget("state")
                    ent.config(state="normal")
                    ent.delete(0, tk.END)
                    ent.config(state=st)
                except Exception:
                    ent.delete(0, tk.END)
            urgency_var.set(False)
            for k in issue_fields:
                issue_vars[k].set(0)
            no_issue_var.set(False)
            total_loss_var.set(False)

        def _collect_form():
            return {
                "board_id": entries["board_id"].get().strip(),
                "name": entries["name"].get().strip(),
                "ic": entries["ic"].get().strip(),
                "dc": entries["dc"].get().strip(),
                "size": entries["size"].get().strip(),
                "module_number": entries.get("module_number").get().strip(),
                "board_code": entries.get("board_code").get().strip(),
                "running_no": entries.get("running_no").get().strip(),
                "date_request": entries.get("date_request").get().strip(),
                "do_date": entries.get("do_date").get().strip(),
                "date_repair": entries.get("date_repair").get().strip(),
                "before_photo": entries.get("before_photo").get().strip(),
                "after_photo": entries.get("after_photo").get().strip(),
                "urgency": bool(urgency_var.get()),
            }

        def on_add_new():
            data = _collect_form()
            try:
                board_id = compute_next_board_id()
                issues = {k: int(issue_vars[k].get()) for k in issue_fields}
                if no_issue_var.get():
                    for k in issue_fields:
                        issues[k] = 0
                issues['no_issue'] = bool(no_issue_var.get())
                issues['total_loss'] = bool(total_loss_var.get())
                add_board(
                    board_id,
                    data["name"],
                    data["ic"],
                    data["dc"],
                    data["size"],
                    module_number=(data["module_number"] or None),
                    pixel=(data["size"] or None),
                    board_code=(data["board_code"] or None),
                    running_no=(data["running_no"] or None),
                    date_request=(data["date_request"] or None),
                    do_date=(data["do_date"] or None),
                    date_repair=(data["date_repair"] or None),
                    before_photo=(data["before_photo"] or None),
                    after_photo=(data["after_photo"] or None),
                    urgency=data["urgency"],
                    issues=issues,
                    created_by=current_user,
                )
                set_entry_value(entries["board_id"], board_id)
                refresh_tree()
                messagebox.showinfo("Added", f"Board {board_id} added.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        # Old inline edit flow removed in favor of pop-up dialog

        def on_delete_selected():
            ids = list(selected_ids)
            if not ids:
                # Fallback to focused row if no checkboxes selected
                item = tree.focus()
                if not item:
                    messagebox.showwarning("Select", "Please tick one or more boards to delete.")
                    return
                vals = tree.item(item, "values")
                ids = [str(vals[1])]
            if not messagebox.askyesno("Confirm Delete", f"Delete {len(ids)} selected board(s)?"):
                return
            deleted = 0
            for bid in ids:
                try:
                    if delete_board(str(bid)):
                        deleted += 1
                except Exception:
                    pass
            selected_ids.clear()
            refresh_tree()
            if deleted:
                messagebox.showinfo("Deleted", f"Deleted {deleted} board(s).")
            else:
                messagebox.showwarning("Not found", "No boards were deleted.")

        def open_view_dialog():
            item = tree.focus()
            if not item:
                messagebox.showwarning("Select", "Please select a board to view.")
                return
            vals = tree.item(item, "values")
            board_id = vals[1]
            b = find_board_by_id(board_id)
            if not b:
                messagebox.showwarning("Not found", "Board not found.")
                return
            win = tk.Toplevel(frm_root)
            win.title(f"Board Details - {board_id}")
            try:
                import os
                ico_path = os.path.join(os.path.dirname(__file__), 'assets', 'app.ico')
                if os.path.exists(ico_path):
                    win.iconbitmap(ico_path)
            except Exception:
                pass
            container = ttk.Frame(win)
            container.pack(fill="both", expand=True, padx=12, pady=12)

            def yn(v: bool) -> str:
                # Use heavier check/cross for clarity
                return "✔" if bool(v) else "✘"

            # Build table headers across the top
            headers = [
                "Board ID",
                "Site Name",
                "IC",
                "DC",
                "Size",
                "Module Number",
                "Pixel",
                "Board Code",
                "Running No",
                "Date Request",
                "DO Date",
                "Date Repair",
                "Before Photo",
                "After Photo",
                "Urgency",
                "Added by",
                "No issue",
                "Total loss",
            ] + issue_fields

            iss = b.get("issues") or {}
            values = [
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
                yn(iss.get('no_issue', False)),
                yn(iss.get('total_loss', False)),
            ] + [str(iss.get(k, 0)) for k in issue_fields]

            # Treeview table with headings and horizontal scrollbar
            tv_frame = ttk.Frame(container)
            tv_frame.pack(fill="both", expand=True)
            detail_tree = ttk.Treeview(tv_frame, columns=headers, show="headings", height=1)
            xscroll = ttk.Scrollbar(tv_frame, orient="horizontal", command=detail_tree.xview)
            detail_tree.configure(xscrollcommand=xscroll.set)
            # Configure columns
            for h in headers:
                detail_tree.heading(h, text=h)
                width = 110
                if h in {"Board ID", "IC", "DC"}: width = 80
                if h in {"Size", "Pixel", "Running No"}: width = 90
                if h in {"Urgency", "No issue", "Total loss"}: width = 80
                if h in {"Before Photo", "After Photo"}: width = 140
                detail_tree.column(h, width=width, stretch=False, anchor="w")
            detail_tree.insert("", "end", values=values)
            detail_tree.pack(fill="both", expand=True)
            xscroll.pack(fill="x")

            # Photos preview panel
            photos = ttk.LabelFrame(container, text="Photos")
            photos.pack(fill="x", padx=6, pady=10)

            def resolve_path(rel_or_abs: str | None) -> str | None:
                if not rel_or_abs:
                    return None
                p = str(rel_or_abs)
                if os.path.isabs(p):
                    return p if os.path.exists(p) else None
                base = _get_data_dir()
                abs_p = os.path.join(base, p)
                return abs_p if os.path.exists(abs_p) else None

            def load_image(path: str | None, max_w=260, max_h=180):
                if not path:
                    return None
                try:
                    from PIL import Image, ImageTk  # Pillow
                    img = Image.open(path)
                    img.thumbnail((max_w, max_h), Image.LANCZOS)
                    return ImageTk.PhotoImage(img)
                except Exception:
                    try:
                        # Fallback for PNG/GIF if Pillow missing
                        return tk.PhotoImage(file=path)
                    except Exception:
                        return None

            before_abs = resolve_path(b.get("before_photo"))
            after_abs = resolve_path(b.get("after_photo"))

            left = ttk.Frame(photos)
            left.pack(side="left", padx=8)
            ttk.Label(left, text="Before").pack(anchor="w")
            before_lbl = ttk.Label(left)
            before_lbl.pack()
            right = ttk.Frame(photos)
            right.pack(side="left", padx=8)
            ttk.Label(right, text="After").pack(anchor="w")
            after_lbl = ttk.Label(right)
            after_lbl.pack()

            win._before_img = load_image(before_abs)
            win._after_img = load_image(after_abs)
            if win._before_img:
                before_lbl.configure(image=win._before_img)
            else:
                before_lbl.configure(text="No photo")
            if win._after_img:
                after_lbl.configure(image=win._after_img)
            else:
                after_lbl.configure(text="No photo")

            def open_file(path):
                if path and os.path.exists(path):
                    try:
                        os.startfile(path)
                    except Exception:
                        pass
            btns = ttk.Frame(photos)
            btns.pack(side="left", padx=8)
            ttk.Button(btns, text="Open Before", command=lambda: open_file(before_abs)).pack(pady=2)
            ttk.Button(btns, text="Open After", command=lambda: open_file(after_abs)).pack(pady=2)

            ttk.Button(container, text="Close", command=win.destroy).pack(anchor="w", padx=6, pady=10)

        def on_select_fill(event=None):
            item = tree.focus()
            if not item:
                return
            vals = tree.item(item, "values")
            entries["board_id"].delete(0, tk.END)
            entries["board_id"].insert(0, vals[1])
            entries["name"].delete(0, tk.END)
            entries["name"].insert(0, vals[2])
            entries["ic"].delete(0, tk.END)
            entries["ic"].insert(0, vals[3])
            entries["dc"].delete(0, tk.END)
            entries["dc"].insert(0, vals[4])
            entries["size"].delete(0, tk.END)
            entries["size"].insert(0, vals[5])
            # load issues for this board if available
            b = find_board_by_id(vals[1])
            if b:
                # Extended fields
                entries.get("board_code").delete(0, tk.END)
                entries.get("board_code").insert(0, b.get("board_code") or "")
                entries.get("module_number").delete(0, tk.END)
                entries.get("module_number").insert(0, b.get("module_number") or "")
                entries.get("running_no").delete(0, tk.END)
                entries.get("running_no").insert(0, b.get("running_no") or "")
                entries.get("date_request").delete(0, tk.END)
                entries.get("date_request").insert(0, b.get("date_request") or "")
                entries.get("do_date").delete(0, tk.END)
                entries.get("do_date").insert(0, b.get("do_date") or "")
                entries.get("date_repair").delete(0, tk.END)
                entries.get("date_repair").insert(0, b.get("date_repair") or "")
                # Photo fields
                entries.get("before_photo").delete(0, tk.END)
                entries.get("before_photo").insert(0, b.get("before_photo") or "")
                entries.get("after_photo").delete(0, tk.END)
                entries.get("after_photo").insert(0, b.get("after_photo") or "")
                try:
                    urgency_var.set(bool(b.get("urgency", False)))
                except Exception:
                    urgency_var.set(False)
                iss = b.get("issues") or {}
                for k in issue_fields:
                    try:
                        issue_vars[k].set(int(iss.get(k, 0)))
                    except Exception:
                        issue_vars[k].set(0)
                try:
                    no_issue_var.set(bool(iss.get('no_issue', False)))
                except Exception:
                    no_issue_var.set(False)
                try:
                    total_loss_var.set(bool(iss.get('total_loss', False)))
                except Exception:
                    total_loss_var.set(False)

        def open_add_dialog():
            win = tk.Toplevel(frm_root)
            win.title("Add Board")
            try:
                import os
                ico_path = os.path.join(os.path.dirname(__file__), 'assets', 'app.ico')
                if os.path.exists(ico_path):
                    win.iconbitmap(ico_path)
            except Exception:
                pass
            frm = ttk.Frame(win)
            frm.pack(fill="both", expand=True, padx=10, pady=10)
            entries_local = {}
            def add_field(label, key, tooltip: str | None = None, is_date=False, is_file=False):
                r = len(entries_local)
                ttk.Label(frm, text=label+":").grid(row=r, column=0, sticky="w", padx=6, pady=4)
                if is_date:
                    container = ttk.Frame(frm); container.grid(row=r, column=1, sticky="w", padx=6, pady=4)
                    ent = ttk.Entry(container, width=30); ent.pack(side="left")
                    def setter(val, e=ent): e.delete(0, tk.END); e.insert(0, val)
                    ttk.Button(container, text="📅", width=3, command=lambda e=ent: open_date_picker(lambda v: setter(v), ent.get() or None)).pack(side="left", padx=4)
                elif is_file:
                    container = ttk.Frame(frm); container.grid(row=r, column=1, sticky="w", padx=6, pady=4)
                    ent = ttk.Entry(container, width=30); ent.pack(side="left")
                    def browse(e=ent):
                        path = filedialog.askopenfilename(title="Select Image", filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All files", "*.*")])
                        if path:
                            e.delete(0, tk.END); e.insert(0, path)
                    ttk.Button(container, text="Browse", command=browse).pack(side="left", padx=4)
                else:
                    ent = ttk.Entry(frm, width=36); ent.grid(row=r, column=1, sticky="w", padx=6, pady=4)
                entries_local[key] = ent
                if tooltip:
                    q = ttk.Label(frm, text="?", width=2, foreground="#555"); q.grid(row=r, column=2, sticky="w"); ToolTip(q, tooltip)

            add_field("Site Name", "name", "Location/site name")
            add_field("IC", "ic", "Controller IC (e.g., SM1627P)")
            add_field("DC", "dc", "Driver IC (e.g., 74HC368)")
            add_field("Size", "size", "Module size (e.g., 64x64)")
            add_field("Module Number", "module_number", "Module/unit number")
            add_field("Board Code", "board_code", "Internal board code")
            # Running number split into two inputs and concatenated on save
            r = len(entries_local)
            ttk.Label(frm, text="Running No:").grid(row=r, column=0, sticky="w", padx=6, pady=4)
            rn_frame = ttk.Frame(frm); rn_frame.grid(row=r, column=1, sticky="w", padx=6, pady=4)
            ent_rn1 = ttk.Entry(rn_frame, width=12)
            ent_rn1.pack(side="left")
            ttk.Label(rn_frame, text=" ").pack(side="left")
            ent_rn2 = ttk.Entry(rn_frame, width=18)
            ent_rn2.pack(side="left")
            entries_local["running_no_p1"] = ent_rn1
            entries_local["running_no_p2"] = ent_rn2
            add_field("Date Request", "date_request", is_date=True)
            add_field("DO Date", "do_date", is_date=True)
            add_field("Date Repair", "date_repair", is_date=True)
            add_field("Before Photo", "before_photo", is_file=True)
            add_field("After Photo", "after_photo", is_file=True)
            urg_local = tk.BooleanVar(value=False)
            ttk.Checkbutton(frm, text="Urgency", variable=urg_local).grid(row=len(entries_local), column=0, padx=6, pady=4, sticky="w")

            # Issues local state
            issue_vars_local = {k: tk.IntVar(value=0) for k in issue_fields}
            no_issue_local = tk.BooleanVar(value=False)
            total_loss_local = tk.BooleanVar(value=False)
            def open_issues_local():
                win2 = tk.Toplevel(win); win2.title("Issues")
                container = ttk.Frame(win2); container.pack(fill="both", expand=True, padx=10, pady=10)
                chk = ttk.Frame(container); chk.grid(row=0, column=0, columnspan=2, sticky="w")
                def apply_state():
                    if no_issue_local.get():
                        for k in issue_fields: issue_vars_local[k].set(0)
                ttk.Checkbutton(chk, text="No issue", variable=no_issue_local, command=apply_state).pack(side="left", padx=6)
                ttk.Checkbutton(chk, text="Total loss", variable=total_loss_local).pack(side="left", padx=6)
                for idx, key in enumerate(issue_fields, start=1):
                    ttk.Label(container, text=key+":").grid(row=idx, column=0, sticky="w", padx=6, pady=4)
                    tk.Spinbox(container, from_=0, to=999, width=8, textvariable=issue_vars_local[key]).grid(row=idx, column=1, sticky="w", padx=6, pady=4)
                ttk.Button(container, text="Close", command=win2.destroy).grid(row=len(issue_fields)+2, column=0, padx=6, pady=10, sticky="w")
            ttk.Button(frm, text="Issues...", command=open_issues_local).grid(row=len(entries_local)+1, column=0, padx=6, pady=6, sticky="w")

            # Quantity for Add Multiple
            ttk.Label(frm, text="Quantity:").grid(row=len(entries_local)+2, column=0, padx=6, pady=4, sticky="w")
            qty_var = tk.IntVar(value=1)
            tk.Spinbox(frm, from_=1, to=500, width=6, textvariable=qty_var).grid(row=len(entries_local)+2, column=1, padx=6, pady=4, sticky="w")

            def on_ok():
                data = {k: entries_local[k].get().strip() for k in entries_local}
                try:
                    qty = int(qty_var.get() or 1)
                    if qty < 1: qty = 1
                except Exception:
                    qty = 1
                issues = {k: int(issue_vars_local[k].get()) for k in issue_fields}
                if no_issue_local.get():
                    for k in issue_fields: issues[k] = 0
                issues['no_issue'] = bool(no_issue_local.get())
                issues['total_loss'] = bool(total_loss_local.get())
                created = []
                try:
                    try:
                        start_module = int((data.get("module_number") or "0").strip() or "0")
                    except Exception:
                        start_module = 0
                    # Compose running number as concatenation of two inputs (no numeric increment)
                    rn_const = (data.get("running_no_p1") or "") + (data.get("running_no_p2") or "")
                    rn_const = rn_const or None
                    for i in range(qty):
                        board_id = compute_next_board_id()
                        mm = str(start_module + i) if start_module or i else (data.get("module_number") or None)
                        rn = rn_const
                        add_board(
                            board_id,
                            data["name"], data["ic"], data["dc"], data["size"],
                            module_number=mm,
                            pixel=(data["size"] or None),
                            board_code=(data["board_code"] or None),
                            running_no=rn,
                            date_request=(data["date_request"] or None),
                            do_date=(data["do_date"] or None),
                            date_repair=(data["date_repair"] or None),
                            before_photo=(data["before_photo"] or None),
                            after_photo=(data["after_photo"] or None),
                            urgency=bool(urg_local.get()),
                            issues=issues,
                            created_by=current_user,
                        )
                        created.append(board_id)
                    refresh_tree()
                    messagebox.showinfo("Added", f"Added {len(created)} board(s): {', '.join(map(str, created))}")
                    win.destroy()
                except Exception as e:
                    messagebox.showerror("Error", str(e))
            ttk.Button(frm, text="OK", command=on_ok).grid(row=len(entries_local)+3, column=1, padx=6, pady=10, sticky="e")
            ttk.Button(frm, text="Cancel", command=win.destroy).grid(row=len(entries_local)+3, column=0, padx=6, pady=10, sticky="w")

        btn_add = ttk.Button(frm_btn, text="Add...", command=open_add_dialog)
        btn_add.pack(side="left", padx=4)

        # Add Multiple is available within the Add dialog; remove toolbar version

        def open_edit_dialog():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Select", "Please select a board to edit.")
                return
            selected_item = sel[0]
            vals = tree.item(selected_item, "values")
            board_id = vals[1]
            existing = find_board_by_id(board_id)
            if not existing:
                messagebox.showwarning("Not found", "Selected board no longer exists.")
                return
            win = tk.Toplevel(frm_root)
            win.title(f"Edit Board - {board_id}")
            try:
                import os
                ico_path = os.path.join(os.path.dirname(__file__), 'assets', 'app.ico')
                if os.path.exists(ico_path):
                    win.iconbitmap(ico_path)
            except Exception:
                pass
            frm = ttk.Frame(win); frm.pack(fill="both", expand=True, padx=10, pady=10)
            entries_local = {}
            def add_field(label, key, val="", is_date=False, is_file=False):
                r = len(entries_local)
                ttk.Label(frm, text=label+":").grid(row=r, column=0, sticky="w", padx=6, pady=4)
                if is_date:
                    container = ttk.Frame(frm); container.grid(row=r, column=1, sticky="w", padx=6, pady=4)
                    ent = ttk.Entry(container, width=30); ent.insert(0, val); ent.pack(side="left")
                    def setter(v, e=ent): e.delete(0, tk.END); e.insert(0, v)
                    ttk.Button(container, text="📅", width=3, command=lambda e=ent: open_date_picker(lambda v: setter(v), ent.get() or None)).pack(side="left", padx=4)
                elif is_file:
                    container = ttk.Frame(frm); container.grid(row=r, column=1, sticky="w", padx=6, pady=4)
                    ent = ttk.Entry(container, width=30); ent.insert(0, val); ent.pack(side="left")
                    def browse(e=ent):
                        path = filedialog.askopenfilename(title="Select Image", filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All files", "*.*")])
                        if path:
                            e.delete(0, tk.END); e.insert(0, path)
                    ttk.Button(container, text="Browse", command=browse).pack(side="left", padx=4)
                else:
                    ent = ttk.Entry(frm, width=36); ent.insert(0, val); ent.grid(row=r, column=1, sticky="w", padx=6, pady=4)
                entries_local[key] = ent
            add_field("Site Name", "name", existing.get("name") or "")
            add_field("IC", "ic", existing.get("ic") or "")
            add_field("DC", "dc", existing.get("dc") or "")
            add_field("Size", "size", existing.get("size") or "")
            add_field("Module Number", "module_number", existing.get("module_number") or "")
            add_field("Board Code", "board_code", existing.get("board_code") or "")
            add_field("Running No", "running_no", existing.get("running_no") or "")
            add_field("Date Request", "date_request", existing.get("date_request") or "", is_date=True)
            add_field("DO Date", "do_date", existing.get("do_date") or "", is_date=True)
            add_field("Date Repair", "date_repair", existing.get("date_repair") or "", is_date=True)
            add_field("Before Photo", "before_photo", existing.get("before_photo") or "", is_file=True)
            add_field("After Photo", "after_photo", existing.get("after_photo") or "", is_file=True)
            urg_local = tk.BooleanVar(value=bool(existing.get("urgency", False)))
            ttk.Checkbutton(frm, text="Urgency", variable=urg_local).grid(row=len(entries_local), column=0, padx=6, pady=4, sticky="w")
            # Issues local
            issue_vars_local = {k: tk.IntVar(value=int((existing.get("issues") or {}).get(k, 0))) for k in issue_fields}
            no_issue_local = tk.BooleanVar(value=bool((existing.get("issues") or {}).get('no_issue', False)))
            total_loss_local = tk.BooleanVar(value=bool((existing.get("issues") or {}).get('total_loss', False)))
            def open_issues_local():
                w2 = tk.Toplevel(win); w2.title("Issues")
                container = ttk.Frame(w2); container.pack(fill="both", expand=True, padx=10, pady=10)
                ttk.Checkbutton(container, text="No issue", variable=no_issue_local).grid(row=0, column=0, sticky="w", padx=6, pady=6)
                ttk.Checkbutton(container, text="Total loss", variable=total_loss_local).grid(row=0, column=1, sticky="w", padx=6, pady=6)
                for idx, key in enumerate(issue_fields, start=1):
                    ttk.Label(container, text=key+":").grid(row=idx, column=0, sticky="w", padx=6, pady=4)
                    tk.Spinbox(container, from_=0, to=999, width=8, textvariable=issue_vars_local[key]).grid(row=idx, column=1, sticky="w", padx=6, pady=4)
                ttk.Button(container, text="Close", command=w2.destroy).grid(row=len(issue_fields)+2, column=0, padx=6, pady=10, sticky="w")
            ttk.Button(frm, text="Issues...", command=open_issues_local).grid(row=len(entries_local)+1, column=0, padx=6, pady=6, sticky="w")
            def on_ok():
                data = {k: entries_local[k].get().strip() for k in entries_local}
                try:
                    existing2 = find_board_by_id(board_id)
                    if not existing2:
                        messagebox.showwarning("Not found", "Selected board no longer exists.")
                        return
                    before_photo = data["before_photo"] or existing2.get("before_photo") or None
                    after_photo = data["after_photo"] or existing2.get("after_photo") or None
                    delete_board(board_id)
                    issues = {k: int(issue_vars_local[k].get()) for k in issue_fields}
                    if no_issue_local.get():
                        for k in issue_fields: issues[k] = 0
                    issues['no_issue'] = bool(no_issue_local.get())
                    issues['total_loss'] = bool(total_loss_local.get())
                    add_board(
                        board_id,
                        data["name"], data["ic"], data["dc"], data["size"],
                        module_number=(data["module_number"] or None),
                        pixel=(data["size"] or None),
                        board_code=(data["board_code"] or None),
                        running_no=(data["running_no"] or None),
                        date_request=(data["date_request"] or None),
                        do_date=(data["do_date"] or None),
                        date_repair=(data["date_repair"] or None),
                        before_photo=before_photo,
                        after_photo=after_photo,
                        urgency=bool(urg_local.get()),
                        issues=issues,
                        created_by=current_user,
                    )
                    refresh_tree(); messagebox.showinfo("Updated", f"Board {board_id} updated."); win.destroy()
                except Exception as e:
                    messagebox.showerror("Error", str(e))
            ttk.Button(frm, text="OK", command=on_ok).grid(row=len(entries_local)+2, column=1, padx=6, pady=10, sticky="e")
            ttk.Button(frm, text="Cancel", command=win.destroy).grid(row=len(entries_local)+2, column=0, padx=6, pady=10, sticky="w")

        btn_edit = ttk.Button(frm_btn, text="Edit...", command=open_edit_dialog)
        btn_edit.pack(side="left", padx=4)

        btn_view = ttk.Button(frm_btn, text="View", command=open_view_dialog)
        btn_view.pack(side="left", padx=4)

        btn_del = ttk.Button(frm_btn, text="Delete Selected", command=on_delete_selected)
        btn_del.pack(side="left", padx=4)

        btn_ref = ttk.Button(frm_btn, text="Refresh", command=refresh_tree)
        btn_ref.pack(side="left", padx=4)

        btn_issues = ttk.Button(frm_btn, text="Issues...", command=open_issues_dialog)
        btn_issues.pack(side="left", padx=4)

        # Single handler: toggle only when clicking the first (Select) column
        def on_tree_click(event):
            col = tree.identify_column(event.x)
            row = tree.identify_row(event.y)
            if col == "#1" and row:
                vals = tree.item(row, "values")
                bid = str(vals[1])
                # Toggle selection set
                if bid in selected_ids:
                    selected_ids.remove(bid)
                else:
                    selected_ids.add(bid)
                new_chk = "☑" if bid in selected_ids else "☐"
                tree.item(row, values=(new_chk,)+tuple(vals[1:]))
                return
            # Ignore clicks on other columns to avoid accidental deselect
        tree.bind("<Button-1>", on_tree_click, add="+")

        # Open read-only viewer window
        def open_viewer_window():
            try:
                from viewer_gui import run_viewer as _run_viewer
                _run_viewer(list_boards=list_boards)
            except Exception as e:
                messagebox.showerror("Viewer", f"Unable to open viewer: {e}")
        ttk.Button(frm_btn, text="Open Viewer...", command=open_viewer_window).pack(side="right", padx=4)

        # No auto-fill into a static form; selection only toggles checkboxes
        refresh_tree()

    # Employees tab moved to employees_gui to keep separation of concerns
    from employees_gui import add_employees_tab

    def show_app():
        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True)
        show_boards_tab(nb)
        if current_role == "admin":
            add_employees_tab(
                nb,
                list_employees=list_employees,
                add_or_update_employee=add_or_update_employee,
                delete_employee=delete_employee,
            )

    def do_login(u: str, p: str):
        nonlocal current_user, current_role
        if u == "admin" and p == "Too@686868":
            current_user = u
            current_role = "admin"
            for w in root.winfo_children():
                if isinstance(w, tk.Frame) or isinstance(w, ttk.Frame):
                    w.destroy()
            show_app()
            return
        e = find_employee(u)
        if e and e.get("password") == p:
            current_user = u
            current_role = "employee"
            for w in root.winfo_children():
                if isinstance(w, tk.Frame) or isinstance(w, ttk.Frame):
                    w.destroy()
            show_app()
            return
        messagebox.showerror("Login failed", "Invalid username or password")

    def show_login():
        frm = ttk.Frame(root)
        frm.pack(fill="both", expand=True, padx=20, pady=20)
        ttk.Label(frm, text="Login", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=10)
        grid = ttk.Frame(frm)
        grid.pack(anchor="w")
        ttk.Label(grid, text="Username:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ent_username = ttk.Entry(grid, width=30)
        ent_username.grid(row=0, column=1, padx=6, pady=6)
        ttk.Label(grid, text="Password:").grid(row=1, column=0, padx=6, pady=6, sticky="w")
        ent_password = ttk.Entry(grid, width=30, show="*")
        ent_password.grid(row=1, column=1, padx=6, pady=6)
        def on_login():
            u = ent_username.get().strip()
            p = ent_password.get().strip()
            do_login(u, p)
        btn = ttk.Button(frm, text="Login", command=on_login)
        btn.pack(pady=12)
        ent_username.focus_set()

    show_login()
    root.mainloop()
