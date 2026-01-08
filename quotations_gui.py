import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime as _dt
import os
from typing import Callable, List, Dict, Any


def run_quotations(parent: tk.Widget, list_boards: Callable[[], List[Dict[str, Any]]]):
    """
    Build a Quotations page inside the given parent widget.

    - Left: Boards from database with basic filters and selection
    - Right: Current quotation items
    - Actions: Add to quotation, remove, clear, and Export to Excel (.xlsx) with CSV fallback
    """
    # Root container for this page
    page = ttk.Frame(parent)
    page.pack(fill="both", expand=True)

    style = ttk.Style(page)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Layout: two columns
    page.columnconfigure(0, weight=1)
    page.columnconfigure(1, weight=1)
    page.rowconfigure(1, weight=1)

    ttk.Label(page, text="Quotations", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 6))

    # Left: boards list
    left = ttk.LabelFrame(page, text="Boards")
    left.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))

    # Search + Filter + Sort bar
    search_var = tk.StringVar(value="")
    sort_var = tk.StringVar(value="Running No Right (Asc)")
    site_var = tk.StringVar(value="All")
    size_var = tk.StringVar(value="All")
    # Month filter state for Date Request
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    month_vars = {m: tk.BooleanVar(value=False) for m in month_names}
    bar = ttk.Frame(left)
    bar.pack(fill="x", padx=8, pady=6)
    ttk.Label(bar, text="Search:").pack(side="left")
    ent_search = ttk.Entry(bar, textvariable=search_var, width=28)
    ent_search.pack(side="left", padx=6)
    ttk.Button(bar, text="Filter...", command=lambda: open_filters_dialog()).pack(side="left", padx=6)
    ttk.Button(bar, text="Sort...", command=lambda: open_sort_dialog()).pack(side="left", padx=6)

    # Tree for boards
    # Multi-select via checkbox column
    selected_ids: set[str] = set()
    cols = ("Select", "Board ID", "Site Name", "Running No Right", "Size")
    tv_boards = ttk.Treeview(left, columns=cols, show="headings", height=12, selectmode="extended")
    def toggle_select_all():
        iids = tv_boards.get_children()
        all_ids = {iid.split(":", 1)[1] if ":" in iid else iid for iid in iids}
        if len(selected_ids) == len(all_ids) and len(all_ids) > 0:
            selected_ids.clear()
        else:
            selected_ids.clear(); selected_ids.update(all_ids)
        refresh_boards()
    for c in cols:
        if c == "Select":
            tv_boards.heading(c, text=c, command=toggle_select_all)
            w = 60
        else:
            tv_boards.heading(c, text=c)
            w = 100
            if c == "Site Name":
                w = 180
            if c == "Running No Right":
                w = 120
        tv_boards.column(c, width=w, stretch=False)
    tv_boards.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # Right: quotation items
    right = ttk.LabelFrame(page, text="Quotation Items")
    right.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(0, 10))

    # Quotation list includes Issue and Quantity (editable)
    q_cols = ("Board ID", "Module No", "RN No", "Issue", "Quantity")
    tv_quote = ttk.Treeview(right, columns=q_cols, show="headings", height=12, selectmode="extended")
    for c in q_cols:
        tv_quote.heading(c, text=c)
        w = 100
        if c in ("Issue",):
            w = 140
        if c in ("Module No", "RN No"):
            w = 90
        tv_quote.column(c, width=w, stretch=False)
    tv_quote.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # Button row
    actions = ttk.Frame(page)
    actions.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
    actions.columnconfigure(0, weight=1)
    actions.columnconfigure(1, weight=1)

    btn_add = ttk.Button(actions, text="Add Selected →")
    btn_remove = ttk.Button(actions, text="← Remove Selected")
    btn_clear = ttk.Button(actions, text="Clear")
    btn_export = ttk.Button(actions, text="Export…")
    btn_add.grid(row=0, column=0, sticky="w", padx=4)
    btn_remove.grid(row=0, column=0, sticky="e", padx=4)
    btn_clear.grid(row=0, column=1, sticky="w", padx=4)
    btn_export.grid(row=0, column=1, sticky="e", padx=4)

    # Helpers
    def _matches(b: Dict[str, Any], q: str) -> bool:
        if not q:
            return True
        ql = q.lower()
        for k in ("board_id", "name", "running_no", "size", "running_no_p1", "running_no_p2"):
            v = b.get(k)
            if v and ql in str(v).lower():
                return True
        return False

    def unique_values(key: str):
        try:
            vals = sorted({(str(b.get(key)) or "") for b in list_boards() if b.get(key)})
            return ["All"] + vals
        except Exception:
            return ["All"]

    def open_filters_dialog():
        win = tk.Toplevel(page)
        win.title("Filters")
        frm = ttk.Frame(win); frm.pack(fill="both", expand=True, padx=10, pady=10)
        ttk.Label(frm, text="Site:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Label(frm, text="Size:").grid(row=0, column=2, sticky="w", padx=6, pady=4)
        site_cb = ttk.Combobox(frm, width=24, textvariable=site_var, state="readonly", values=unique_values("name"))
        size_cb = ttk.Combobox(frm, width=12, textvariable=size_var, state="readonly", values=unique_values("size"))
        site_cb.grid(row=0, column=1, sticky="w", padx=6, pady=4)
        size_cb.grid(row=0, column=3, sticky="w", padx=6, pady=4)
        # Month checkboxes by Date Request
        ttk.Label(frm, text="Months (Date Request):").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        months_frame = ttk.Frame(frm)
        months_frame.grid(row=1, column=1, columnspan=3, sticky="w", padx=6, pady=4)
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
        def on_ok():
            refresh_boards(); win.destroy()
        ttk.Button(frm, text="OK", command=on_ok).grid(row=1, column=3, sticky="e", padx=6, pady=8)
        ttk.Button(frm, text="Clear", command=lambda: [site_var.set("All"), size_var.set("All"), clear_all_months(), refresh_boards()]).grid(row=1, column=2, sticky="e", padx=6, pady=8)

    def open_sort_dialog():
        win = tk.Toplevel(page)
        win.title("Sort")
        frm = ttk.Frame(win); frm.pack(fill="both", expand=True, padx=10, pady=10)
        ttk.Label(frm, text="Sort by:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        options = [
            "Running No Right (Asc)",
            "Running No Right (Desc)",
            "Date Request (Newest)",
            "Date Request (Oldest)",
            "Module Number (Asc)",
            "Module Number (Desc)",
            "Site Name (A-Z)",
        ]
        cb = ttk.Combobox(frm, width=26, textvariable=sort_var, state="readonly", values=options)
        cb.grid(row=0, column=1, sticky="w", padx=6, pady=4)
        ttk.Button(frm, text="OK", command=lambda: [refresh_boards(), win.destroy()]).grid(row=1, column=1, sticky="e", padx=6, pady=8)

    def refresh_boards():
        tv_boards.delete(*tv_boards.get_children())
        query = search_var.get().strip()
        try:
            data = list_boards()
        except Exception as e:
            messagebox.showerror("Error", f"Unable to list boards: {e}")
            data = []
        # Apply filters
        s = site_var.get()
        if s and s != "All":
            data = [b for b in data if str(b.get("name")) == s]
        sz = size_var.get()
        if sz and sz != "All":
            data = [b for b in data if str(b.get("size")) == sz]
        # Months by date_request
        if month_vars:
            sel_months = [m for m, var in month_vars.items() if var.get()]
            if sel_months:
                mindex = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
                nums = {mindex[m] for m in sel_months}
                def dm(b):
                    d = b.get("date_request")
                    if not d:
                        return None
                    try:
                        return int(str(d).split("-")[1])
                    except Exception:
                        return None
                data = [b for b in data if dm(b) in nums]
        # Apply search
        data = [b for b in data if _matches(b, query)]
        # Sort
        def keydate(b):
            import datetime as _dt
            try:
                return _dt.datetime.strptime(str(b.get("date_request")), "%Y-%m-%d")
            except Exception:
                return _dt.datetime(1900, 1, 1)
        def keyint(b, k):
            try:
                return int(str(b.get(k) or "0"))
            except Exception:
                return 0
        if sort_var.get() == "Running No Right (Asc)":
            data.sort(key=lambda b: keyint(b, "running_no_p2"))
        elif sort_var.get() == "Running No Right (Desc)":
            data.sort(key=lambda b: keyint(b, "running_no_p2"), reverse=True)
        elif sort_var.get() == "Date Request (Newest)":
            data.sort(key=keydate, reverse=True)
        elif sort_var.get() == "Date Request (Oldest)":
            data.sort(key=keydate)
        elif sort_var.get() == "Module Number (Asc)":
            data.sort(key=lambda b: keyint(b, "module_number"))
        elif sort_var.get() == "Module Number (Desc)":
            data.sort(key=lambda b: keyint(b, "module_number"), reverse=True)
        elif sort_var.get() == "Site Name (A-Z)":
            data.sort(key=lambda b: str(b.get("name") or ""))
        # Populate
        for b in data:
            bid = str(b.get("board_id"))
            chk = "☑" if bid in selected_ids else "☐"
            rn_right = str(b.get("running_no_p2") or "") or (str(b.get("running_no") or ""))
            rn_right = rn_right if rn_right else "-"
            tv_boards.insert("", "end", iid=f"b:{bid}", values=(chk, bid, b.get("name") or "", rn_right, b.get("size") or ""))

    def _get_board_by_id(board_id: str) -> Dict[str, Any] | None:
        try:
            for b in list_boards():
                if str(b.get("board_id")) == str(board_id):
                    return b
        except Exception:
            return None
        return None

    def add_selected_to_quote():
        # Prefer checkbox selections; fallback to row selection
        rows_to_add = []
        if selected_ids:
            for bid in list(selected_ids):
                iid = f"b:{bid}"
                if tv_boards.exists(iid):
                    rows_to_add.append(tv_boards.item(iid, "values"))
        else:
            sel = tv_boards.selection()
            for iid in sel:
                rows_to_add.append(tv_boards.item(iid, "values"))
        if not rows_to_add:
            messagebox.showinfo("Add", "Select one or more boards to add.")
            return
        for vals in rows_to_add:
            # vals: (chk, bid, site, rn_right, size)
            bid = str(vals[1])
            b = _get_board_by_id(bid) or {}
            module_no = b.get("module_number") or "-"
            rn_right = vals[3]
            issue = ""  # admin can fill later
            qty = 1
            tv_quote.insert("", "end", values=(bid, module_no, rn_right, issue, qty))

    def remove_selected_from_quote():
        sel = tv_quote.selection()
        for iid in sel:
            tv_quote.delete(iid)

    def clear_quote():
        tv_quote.delete(*tv_quote.get_children())

    def export_quote():
        # Gather rows
        rows = [tv_quote.item(i, "values") for i in tv_quote.get_children()]
        if not rows:
            messagebox.showinfo("Export", "Quotation list is empty.")
            return
        # Prompt for metadata: quotation id, project name/code, modules code, total repair modules, date request
        def prompt_meta(defaults: dict) -> dict | None:
            win = tk.Toplevel(page); win.title("Quotation Details")
            frm = ttk.Frame(win); frm.pack(fill="both", expand=True, padx=10, pady=10)
            fields = [
                ("Quotation ID", "quotation_id"),
                ("Project Name", "project_name"),
                ("Project Code", "project_code"),
                ("Modules Code", "modules_code"),
                ("Total Repair Modules", "total_repair_modules"),
                ("Date Request (dd/mm/yyyy)", "date_request"),
            ]
            vars: dict[str, tk.StringVar] = {}
            for r, (label, key) in enumerate(fields):
                ttk.Label(frm, text=label+":").grid(row=r, column=0, sticky="w", padx=6, pady=4)
                v = tk.StringVar(value=str(defaults.get(key, "")))
                ttk.Entry(frm, textvariable=v, width=30).grid(row=r, column=1, sticky="w", padx=6, pady=4)
                vars[key] = v
            result: dict | None = {k: v.get().strip() for k, v in vars.items()}
            def ok():
                nonlocal result
                result = {k: v.get().strip() for k, v in vars.items()}
                win.destroy()
            def cancel():
                nonlocal result
                result = None
                win.destroy()
            btns = ttk.Frame(frm); btns.grid(row=len(fields), column=0, columnspan=2, sticky="e")
            ttk.Button(btns, text="Cancel", command=cancel).pack(side="left", padx=6)
            ttk.Button(btns, text="OK", command=ok).pack(side="left", padx=6)
            win.grab_set(); page.wait_window(win)
            return result

        computed_total = 0
        for r in rows:
            try:
                computed_total += int(r[4])
            except Exception:
                pass
        defaults = {
            "quotation_id": "1",
            "project_name": "",
            "project_code": "",
            "modules_code": "",
            "total_repair_modules": str(computed_total or len(rows)),
            "date_request": _dt.date.today().strftime('%d/%m/%Y'),
        }
        meta = prompt_meta(defaults)
        if meta is None:
            return
        # Choose file
        path = filedialog.asksaveasfilename(
            title="Export Quotation",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", ".xlsx"), ("CSV", ".csv")],
        )
        if not path:
            return
        if path.lower().endswith(".xlsx"):
            try:
                export_to_xlsx(path, rows, meta)
                messagebox.showinfo("Export", f"Saved to {path}")
                return
            except Exception as e:
                messagebox.showwarning("Excel export failed", f"Falling back to CSV. Error: {e}")
                # Fall through to CSV
        try:
            export_to_csv(path if path.lower().endswith('.csv') else path + '.csv', rows, meta)
            messagebox.showinfo("Export", f"Saved to {path if path.lower().endswith('.csv') else path + '.csv'}")
        except Exception as e:
            messagebox.showerror("Export", f"Failed to export: {e}")

    def export_to_xlsx(path: str, rows, meta: dict):
        try:
            from openpyxl import Workbook  # type: ignore
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side  # type: ignore
        except Exception as e:
            raise RuntimeError("openpyxl is required for .xlsx export") from e
        wb = Workbook()
        # Split rows into pages (item rows per page)
        page_size = 10
        pages = [rows[i:i+page_size] for i in range(0, len(rows), page_size)] or [[]]
        from openpyxl.utils import get_column_letter  # type: ignore
        # Try to load a logo image if available
        logo_path_candidates = [
            os.path.join(os.path.dirname(__file__), 'assets', 'IDS LOGO.png'),
            os.path.join(os.path.dirname(__file__), 'assets', 'logo.png'),
            os.path.join(os.path.dirname(__file__), 'assets', 'logo.jpg'),
        ]
        logo_path = next((p for p in logo_path_candidates if os.path.exists(p)), None)
        for page_index, page_rows in enumerate(pages, start=1):
            ws = wb.active if page_index == 1 else wb.create_sheet()
            ws.title = f"Page {page_index}"
            # Hide default Excel gridlines to match printed look
            ws.sheet_view.showGridLines = False
            r = 1
            # Header with optional logo and company title
            if logo_path:
                try:
                    from openpyxl.drawing.image import Image as XLImage  # type: ignore
                    img = XLImage(logo_path)
                    img.height = 60
                    img.width = 100
                    ws.add_image(img, "A1")
                except Exception:
                    pass
            # Company name line
            ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=9)
            c = ws.cell(row=r, column=2, value="IDS BEYOND MEDIA SDN BHD")
            c.font = Font(b=True, size=14)
            r += 1
            # Optional address line (simple placeholder to mimic layout)
            ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=9)
            ws.cell(row=r, column=2, value="Website: www.megascreen.com.my   Tel: 601-657 3233   Fax: 604-656 1318")
            r += 2
            # Quotation meta (box on the right)
            ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=9)
            ws.cell(row=r, column=7, value=f"QUOTATION NO: {meta.get('quotation_id','')}").font = Font(b=True)
            r += 1
            ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=9)
            ws.cell(row=r, column=7, value=f"Date: {_dt.date.today().strftime('%d-%b-%y')}")
            r += 1
            ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=9)
            ws.cell(row=r, column=7, value=f"Page: {page_index}/{len(pages)}")
            r += 2
            # Title centered
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)
            ws.cell(row=r, column=1, value="QUOTATION").font = Font(b=True, size=12)
            ws.cell(row=r, column=1).alignment = Alignment(horizontal="center")
            r += 2

            # Project/Remark boxes
            thin = Side(style="thin", color="000000")
            border_all = Border(left=thin, right=thin, top=thin, bottom=thin)
            # Project name/code on left
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
            ws.cell(row=r, column=1, value=f"Project Name: {meta.get('project_name','')}").border = border_all
            ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=9)
            ws.cell(row=r, column=6, value=f"Remark    : Modules Code: {meta.get('modules_code','')}").border = border_all
            r += 1
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
            ws.cell(row=r, column=1, value=f"Project Code: {meta.get('project_code','')}").border = border_all
            ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=9)
            ws.cell(row=r, column=6, value=f"Total Repair Modules : {meta.get('total_repair_modules','')}pcs").border = border_all
            r += 1

            # Date Request and Pixel row
            thin = Side(style="thin", color="000000")
            border_all = Border(left=thin, right=thin, top=thin, bottom=thin)
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
            ws.cell(row=r, column=1, value="Date Request").border = border_all
            ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
            ws.cell(row=r, column=3, value=meta.get('date_request','')).border = border_all
            ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=7)
            ws.cell(row=r, column=6, value="Pixel").border = border_all
            ws.merge_cells(start_row=r, start_column=8, end_row=r, end_column=9)
            ws.cell(row=r, column=8, value="").border = border_all
            r += 2

            # Table headers styled
            headers = ["Item", "Module No", "RN No", "Issue", "Quantity"]
            fill_grey = PatternFill("solid", fgColor="DDDDDD")
            start_col = 1
            for idx, h in enumerate(headers):
                col_idx = start_col + idx
                ws.cell(row=r, column=col_idx, value=h).font = Font(b=True)
                ws.cell(row=r, column=col_idx).alignment = Alignment(horizontal="center")
                ws.cell(row=r, column=col_idx).fill = fill_grey
                # Only outer borders to reduce column lines
                header_border = Border(
                    left=thin if col_idx == start_col else Side(style=None),
                    right=thin if col_idx == start_col + len(headers) - 1 else Side(style=None),
                    top=thin,
                    bottom=thin,
                )
                ws.cell(row=r, column=col_idx).border = header_border
                ws.column_dimensions[get_column_letter(col_idx)].width = 16 if h in ("Issue", "Module No") else 12
            r += 1

            # Table rows (outer box borders only; remove internal column lines)
            for idx, v in enumerate(page_rows, start=1 + (page_index-1)*page_size):
                # v = (Board ID, Module No, RN No, Issue, Quantity)
                for col_idx, val in enumerate([idx, v[1], v[2], v[3]], start=1):
                    border = Border(
                        left=thin if col_idx == start_col else Side(style=None),
                        right=thin if col_idx == start_col + len(headers) - 1 else Side(style=None),
                        top=thin,
                        bottom=thin,
                    )
                    ws.cell(row=r, column=col_idx, value=val).border = border
                try:
                    border_q = Border(
                        left=thin if 5 == start_col else Side(style=None),
                        right=thin if 5 == start_col + len(headers) - 1 else Side(style=None),
                        top=thin,
                        bottom=thin,
                    )
                    ws.cell(row=r, column=5, value=int(v[4])).border = border_q
                except Exception:
                    ws.cell(row=r, column=5, value=v[4]).border = border_q
                r += 1
            # Totals row (Total Repair Modules)
            try:
                total_qty = int(meta.get('total_repair_modules'))
            except Exception:
                total_qty = 0
                for v in rows:
                    try:
                        total_qty += int(v[4])
                    except Exception:
                        pass
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
            ws.cell(row=r, column=1, value="Total Repair Modules (pcs)").font = Font(b=True)
            ws.cell(row=r, column=1).alignment = Alignment(horizontal="right")
            ws.cell(row=r, column=1).border = border_all
            ws.cell(row=r, column=5, value=total_qty).font = Font(b=True)
            ws.cell(row=r, column=5).border = border_all
        wb.save(path)

    def export_to_csv(path: str, rows, meta: dict):
        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Quotation ID", meta.get('quotation_id','')])
            writer.writerow(["Project Name", meta.get('project_name','')])
            writer.writerow(["Project Code", meta.get('project_code','')])
            writer.writerow(["Modules Code", meta.get('modules_code','')])
            writer.writerow(["Total Repair Modules", meta.get('total_repair_modules','')])
            writer.writerow(["Date Request", meta.get('date_request','')])
            writer.writerow([])
            writer.writerow(["Item", "Module No", "RN No", "Issue", "Quantity"])
            for i, r in enumerate(rows, start=1):
                writer.writerow([i, r[1], r[2], r[3], r[4]])

    # Bindings
    btn_add.configure(command=add_selected_to_quote)
    btn_remove.configure(command=remove_selected_from_quote)
    btn_clear.configure(command=clear_quote)
    btn_export.configure(command=export_quote)
    ent_search.bind("<KeyRelease>", lambda _e: refresh_boards())

    # Checkbox toggle only on first column
    def on_tree_click(event):
        col = tv_boards.identify_column(event.x)
        row = tv_boards.identify_row(event.y)
        if col == "#1" and row:
            iid = row
            bid = iid.split(":", 1)[1] if ":" in iid else iid
            if bid in selected_ids:
                selected_ids.remove(bid)
            else:
                selected_ids.add(bid)
            vals = tv_boards.item(iid, "values")
            chk = "☑" if bid in selected_ids else "☐"
            tv_boards.item(iid, values=(chk,) + tuple(vals[1:]))
            return
    tv_boards.bind("<Button-1>", on_tree_click, add="+")

    refresh_boards()

    # Simple in-place editing for Issue and Quantity
    issue_fields = (
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
    )

    def begin_edit(event):
        iid = tv_quote.identify_row(event.y)
        col = tv_quote.identify_column(event.x)
        if not iid or not col:
            return
        col_idx = int(col.replace('#','')) - 1
        bbox = tv_quote.bbox(iid, col)
        if not bbox:
            return
        x, y, w, h = bbox
        vals = list(tv_quote.item(iid, 'values'))
        # Issue column
        if q_cols[col_idx] == 'Issue':
            top = ttk.Combobox(tv_quote, values=issue_fields, state='readonly')
            top.place(x=x, y=y, width=w, height=h)
            top.set(vals[col_idx])
            def commit(_e=None):
                vals[col_idx] = top.get()
                tv_quote.item(iid, values=tuple(vals))
                top.destroy()
            top.bind('<Return>', commit)
            top.bind('<FocusOut>', commit)
            top.focus_set()
        # Quantity column
        elif q_cols[col_idx] == 'Quantity':
            var = tk.StringVar(value=str(vals[col_idx]))
            ent = ttk.Entry(tv_quote, textvariable=var)
            ent.place(x=x, y=y, width=w, height=h)
            def commit_q(_e=None):
                v = var.get().strip()
                try:
                    v = int(v)
                except Exception:
                    v = v
                vals[col_idx] = v
                tv_quote.item(iid, values=tuple(vals))
                ent.destroy()
            ent.bind('<Return>', commit_q)
            ent.bind('<FocusOut>', commit_q)
            ent.focus_set()

    tv_quote.bind('<Double-1>', begin_edit)

    return page
