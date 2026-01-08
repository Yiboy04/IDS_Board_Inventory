import tkinter as tk
from tkinter import ttk


def run_menu(root, open_boards, open_employees, open_viewer=None, role="admin"):
    """
    Admin-only menu landing page.

    Parameters
    ----------
    root: Tk
        Existing Tk root instance (owned by login_gui).
    open_boards: Callable
        Function to navigate to boards page.
    open_employees: Callable
        Function to navigate to employees page.
    open_viewer: Optional[Callable]
        Function to open viewer page (if provided).
    """
    # Clear current content area
    for w in root.winfo_children():
        if isinstance(w, tk.Frame) or isinstance(w, ttk.Frame):
            w.destroy()

    # Global styles for a modern look
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    primary = "#2563eb"
    primary_dark = "#1e40af"
    accent = "#0ea5e9"
    bg = "#f7f7f9"
    card_bg = "#ffffff"

    style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
    style.configure("Section.TLabel", font=("Segoe UI", 12))
    style.configure("Card.TFrame", background=card_bg, relief="raised", borderwidth=1)
    style.configure("Primary.TButton", font=("Segoe UI", 11), padding=10)
    style.map(
        "Primary.TButton",
        background=[["active", primary_dark]],
        foreground=[["active", "#ffffff"]],
    )

    # Top hero/header
    header = tk.Frame(root, bg=accent)
    header.pack(fill="x")
    title_text = "Admin Menu" if role == "admin" else "Menu"
    tk.Label(header, text=title_text, font=("Segoe UI", 18, "bold"), fg="#ffffff", bg=accent).pack(anchor="w", padx=24, pady=(16, 4))
    subtitle = "Manage boards, employees, and tools" if role == "admin" else "Quick access to add boards"
    tk.Label(header, text=subtitle, font=("Segoe UI", 10), fg="#e6f3ff", bg=accent).pack(anchor="w", padx=24, pady=(0, 16))

    # Content container
    outer = tk.Frame(root, bg=bg)
    outer.pack(fill="both", expand=True)
    container = ttk.Frame(outer)
    container.pack(fill="both", expand=True, padx=24, pady=24)

    ttk.Label(container, text="Quick Actions", style="Section.TLabel").grid(row=0, column=0, sticky="w")

    cards = ttk.Frame(container)
    cards.grid(row=1, column=0, sticky="nw", pady=(8, 0))

    def make_card(parent, title, desc, btn_text, btn_cmd, col):
        card = ttk.Frame(parent, style="Card.TFrame")
        card.grid(row=0, column=col, padx=(0, 16), pady=(0, 16), sticky="nsew")
        card.columnconfigure(0, weight=1)
        ttk.Label(card, text=title, font=("Segoe UI", 12, "bold"), background=card_bg).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))
        ttk.Label(card, text=desc, style="Section.TLabel", background=card_bg).grid(row=1, column=0, sticky="w", padx=12)
        ttk.Button(card, text=btn_text, style="Primary.TButton", command=btn_cmd).grid(row=2, column=0, sticky="w", padx=12, pady=(12, 12))

    # Role-based cards
    col_idx = 0
    if role == "admin":
        make_card(
            cards,
            "Boards",
            "Add, edit, and manage boards",
            "Open Boards",
            open_boards,
            col_idx,
        )
        col_idx += 1
        make_card(
            cards,
            "Employees",
            "Add or update employees",
            "Open Employees",
            open_employees,
            col_idx,
        )
        col_idx += 1
        if open_viewer:
            make_card(
                cards,
                "Viewer",
                "Browse and filter records",
                "Open Viewer",
                open_viewer,
                col_idx,
            )
    else:
        make_card(
            cards,
            "Add Board",
            "Create a new board entry",
            "Go to Add Board",
            open_boards,
            col_idx,
        )

    # Footer / info
    info_text = "More admin tools coming soon…" if role == "admin" else "More tools coming soon…"
    ttk.Label(container, text=info_text, style="Section.TLabel").grid(row=2, column=0, sticky="w", pady=(8, 0))
