#!/usr/bin/env python3
"""
Created by Chamunda with help of Copilot.
"""

import os
import csv
import json
import pyperclip
import calendar
import datetime
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from typing import Dict, List, Tuple, Optional
import customtkinter as ctk

# ---------------- Appearance ----------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ---------------- Data / Config ----------------
SETTINGS_FILE = "settings.json"
DEFAULT_CLAN_NAME = "Desi"

INDIAN_STATES = [
    "Unknown",
    "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat",
    "Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh",
    "Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab",
    "Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh",
    "Uttarakhand","West Bengal",
    "Andaman and Nicobar Islands","Chandigarh","Dadra and Nagar Haveli and Daman and Diu",
    "Delhi","Jammu and Kashmir","Ladakh","Lakshadweep","Puducherry"
]

MAPS = [f"Map {i}" for i in range(1, 13)]
MAPS_7_12 = [f"Map {i}" for i in range(7, 13)]
SERVERS = ["ASIA", "EU", "TR", "USA", "SA"]

TABLES = {
    "Clan": {"file": "clan_table.csv", "headers": ["Tag","Name","State","Map","Role","Status","Discord ID","Note"]},
    "Blacklisted": {"file": "blacklisted_table.csv", "headers": ["Tag","Name","Reason","Note","Proof"]},
    "Removed": {"file": "removed_table.csv", "headers": ["Tag","Name","Reason","Note","Proof"]}
}

PAGE_SIZE = 30
MONSTER_CSV = "monster_hunt.csv"
MONSTER_LOG = "monster_hunt_log.csv"  # audit log

# ---------------- Treeview style helper ----------------
def apply_treeview_style():
    style = ttk.Style()
    try:
        style.theme_use("default")
    except Exception:
        pass
    style.configure("Custom.Treeview",
                    background="#0b0b0b",
                    fieldbackground="#0b0b0b",
                    foreground="#e5e7eb",
                    rowheight=26,
                    bordercolor="#374151",
                    borderwidth=1,
                    relief="flat")
    style.configure("Custom.Treeview.Heading",
                    background="#111827",
                    foreground="#f1c40f",
                    relief="raised")
    style.map("Custom.Treeview",
              background=[("selected", "#1f2937")],
              foreground=[("selected", "#ffffff")])

# ---------------- Settings helpers ----------------
def load_settings() -> Dict:
    if not os.path.exists(SETTINGS_FILE):
        return {"clan_name": DEFAULT_CLAN_NAME}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"clan_name": DEFAULT_CLAN_NAME}
            return {"clan_name": data.get("clan_name", DEFAULT_CLAN_NAME)}
    except Exception:
        return {"clan_name": DEFAULT_CLAN_NAME}

def save_settings(settings: Dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ---------------- Helpers for monster CSV & log ----------------
def ensure_dir_for_file(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def load_monster_csv() -> Dict[str, Dict[str, Dict]]:
    data: Dict[str, Dict[str, Dict]] = {}
    if not os.path.exists(MONSTER_CSV):
        return data
    try:
        with open(MONSTER_CSV, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                month = (row.get("month") or "").strip()
                day = (row.get("day") or "").strip()
                if not month or not day:
                    continue
                if month not in data:
                    data[month] = {}
                members = row.get("members", "")
                try:
                    members_val = int(members) if members != "" else ""
                except Exception:
                    members_val = ""
                data[month][day] = {
                    "members": members_val,
                    "time": row.get("time", "") or "",
                    "map": row.get("map", "") or "",
                    "server": row.get("server", "") or "",
                    "done": (row.get("done", "").strip().lower() in ("1","true","yes","y")),
                    "note": row.get("note", "") or "",
                    "proof": row.get("proof", "") or ""
                }
    except Exception:
        pass
    return data

def prune_keep_recent_months(data: Dict[str, Dict[str, Dict]]):
    try:
        today = datetime.date.today()
        cur_key = f"{today.year:04d}-{today.month:02d}"
        prev_date = (today.replace(day=15) - datetime.timedelta(days=31))
        prev_key = f"{prev_date.year:04d}-{prev_date.month:02d}"
        allowed = {cur_key, prev_key}
        for k in list(data.keys()):
            if k not in allowed:
                data.pop(k, None)
    except Exception:
        pass

def save_monster_csv(data: Dict[str, Dict[str, Dict]]):
    ensure_dir_for_file(MONSTER_CSV)
    try:
        prune_keep_recent_months(data)
        with open(MONSTER_CSV, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["month","day","members","time","map","server","done","note","proof"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for month in sorted(data.keys()):
                for day in sorted(data[month].keys(), key=lambda x: int(x)):
                    rec = data[month][day]
                    writer.writerow({
                        "month": month,
                        "day": day,
                        "members": rec.get("members", ""),
                        "time": rec.get("time", ""),
                        "map": rec.get("map", ""),
                        "server": rec.get("server", ""),
                        "done": "1" if rec.get("done") else "0",
                        "note": rec.get("note", ""),
                        "proof": rec.get("proof", "")
                    })
    except Exception:
        pass

def append_monster_log(action: str, year: int, month: int, day: int, before: Dict = None, after: Dict = None):
    ensure_dir_for_file(MONSTER_LOG)
    try:
        with open(MONSTER_LOG, "a", newline="", encoding="utf-8") as f:
            fieldnames = ["timestamp","action","month","day","before","after"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if f.tell() == 0:
                writer.writeheader()
            ts = datetime.datetime.now().isoformat()
            writer.writerow({
                "timestamp": ts,
                "action": action,
                "month": f"{year:04d}-{month:02d}",
                "day": str(day),
                "before": str(before or {}),
                "after": str(after or {})
            })
    except Exception:
        pass

def read_monster_log() -> List[Dict]:
    if not os.path.exists(MONSTER_LOG):
        return []
    try:
        with open(MONSTER_LOG, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception:
        return []

def undo_last_monster_action() -> Optional[str]:
    logs = read_monster_log()
    if not logs:
        return None
    last = logs[-1]
    try:
        month_key = last.get("month", "")
        day = last.get("day", "")
        before_str = last.get("before", "")
        def safe_eval(s):
            try:
                return eval(s, {"__builtins__": None}, {})
            except Exception:
                return {}
        before = safe_eval(before_str)
        monster_data = load_monster_csv()
        if before:
            if month_key not in monster_data:
                monster_data[month_key] = {}
            monster_data[month_key][day] = before
        else:
            if month_key in monster_data and day in monster_data[month_key]:
                monster_data[month_key].pop(day, None)
        prune_keep_recent_months(monster_data)
        save_monster_csv(monster_data)
        remaining = logs[:-1]
        ensure_dir_for_file(MONSTER_LOG)
        with open(MONSTER_LOG, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["timestamp","action","month","day","before","after"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in remaining:
                writer.writerow(r)
        return f"Undid last action: {last.get('action')} on {month_key}-{day}"
    except Exception as e:
        return f"Failed to undo: {e}"

# ---------------- Utility for heatmap color ----------------
def heatmap_color_for_value(val: int, max_val: int) -> str:
    try:
        if max_val <= 0:
            max_val = 1
        ratio = max(0.0, min(1.0, float(val) / float(max_val)))
        r0, g0, b0 = (10, 10, 10)
        r1, g1, b1 = (22, 163, 74)
        r = int(r0 + (r1 - r0) * ratio)
        g = int(g0 + (g1 - g0) * ratio)
        b = int(b0 + (b1 - b0) * ratio)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#000000"

# ---------------- Main Application ----------------
class DesiClanManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        apply_treeview_style()

        # load settings
        self.settings = load_settings()
        self.clan_name = self.settings.get("clan_name", DEFAULT_CLAN_NAME)

        # UI
        self.title(f"{self.clan_name} Clan — Actions")
        self.geometry("320x520")
        self.resizable(False, False)
        self.configure(fg_color="#050505")

        # state
        self._undo_stack: List[Dict] = []
        self._open_popups: set = set()
        self._view_notify_label: Optional[ctk.CTkLabel] = None

        self._last_view_window: Optional[tk.Toplevel] = None
        self._last_view_tree: Optional[ttk.Treeview] = None
        self._last_view_table_var: Optional[tk.StringVar] = None
        self._last_view_filter_var: Optional[tk.StringVar] = None
        self._last_view_page_var: Optional[tk.IntVar] = None

        # clan label var for dynamic updates
        self.clan_label_var = tk.StringVar(value=f"{self.clan_name} Clan — Actions")

        self._build_action_panel()

        self.bind("<F8>", lambda e: self.quick_add())
        self.bind_all("<Control-f>", lambda e: self.show_search(e))
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        if not os.path.exists(MONSTER_CSV):
            save_monster_csv({})
        if not os.path.exists(MONSTER_LOG):
            append_monster_log("init", datetime.date.today().year, datetime.date.today().month, 0, before={}, after={})

    # ---------------- Action Panel ----------------
    def _build_action_panel(self):
        panel = ctk.CTkFrame(self, fg_color="#0b0b0b", corner_radius=10)
        panel.pack(fill="both", expand=True, padx=10, pady=10)

        # Use clan_label_var so it updates when clan name changes
        ctk.CTkLabel(panel, textvariable=self.clan_label_var, text_color="#f1c40f",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(8, 6))
        ctk.CTkLabel(panel, text="Quick controls for in-game use", text_color="#e5e7eb",
                     font=ctk.CTkFont(size=10)).pack(pady=(0, 8))

        btn_kwargs = {"width": 260, "height": 52, "corner_radius": 8, "font": ctk.CTkFont(size=12, weight="bold")}
        ctk.CTkButton(panel, text="⚔️ Quick Add (F8)", fg_color="#b91c1c", hover_color="#ef4444",
                      command=self.quick_add, **btn_kwargs).pack(pady=(6, 6))
        ctk.CTkButton(panel, text="👁️ View & Manage", fg_color="#6b21a8", hover_color="#7e22ce",
                      command=self.show_view_window, **btn_kwargs).pack(pady=(6, 6))
        ctk.CTkButton(panel, text="🔍 Global Search (Ctrl+F)", fg_color="#1e3a8a", hover_color="#1e40af",
                      command=self.show_search, **btn_kwargs).pack(pady=(6, 6))
        ctk.CTkButton(panel, text="🐉 Monster Hunt", fg_color="#0f766e", hover_color="#115e59",
                      command=self.show_monster_hunt, **btn_kwargs).pack(pady=(6, 6))
        ctk.CTkButton(panel, text="⚙️ Settings", fg_color="#334155", hover_color="#475569",
                      command=self.show_settings, **btn_kwargs).pack(pady=(6, 6))

        status_frame = ctk.CTkFrame(panel, fg_color="transparent")
        status_frame.pack(fill="x", pady=(12, 6))
        self.status = ctk.CTkLabel(status_frame, text="Ready • F8 Quick Add • Ctrl+F Search",
                                   font=ctk.CTkFont(size=9), text_color="#fca5a5")
        self.status.pack(side="left", padx=(8, 6))
        ctk.CTkButton(status_frame, text="☠️ Exit", width=80, height=36,
                      fg_color="#4c1d95", hover_color="#6b21a8",
                      command=self.on_close).pack(side="right", padx=(6, 8))

    # ---------------- CSV helpers for tables ----------------
    def ensure_csv(self, table_name: str):
        if table_name not in TABLES:
            return
        cfg = TABLES[table_name]
        if not os.path.exists(cfg["file"]):
            try:
                ensure_dir_for_file(cfg["file"])
                with open(cfg["file"], "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=cfg["headers"])
                    writer.writeheader()
            except Exception as e:
                messagebox.showerror("File Error", f"Unable to create {cfg['file']}: {e}")

    def load_table(self, table_name: str) -> List[Dict]:
        if table_name not in TABLES:
            return []
        try:
            with open(TABLES[table_name]["file"], "r", newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except FileNotFoundError:
            return []
        except Exception:
            return []

    def load_all_rows(self) -> List[Tuple[str, Dict]]:
        all_rows = []
        for t in TABLES.keys():
            rows = self.load_table(t)
            for r in rows:
                all_rows.append((t, r))
        return all_rows

    def write_table(self, table_name: str, rows: List[Dict]):
        if table_name not in TABLES:
            return
        try:
            ensure_dir_for_file(TABLES[table_name]["file"])
            with open(TABLES[table_name]["file"], "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=TABLES[table_name]["headers"])
                writer.writeheader()
                for r in rows:
                    writer.writerow({h: r.get(h, "") for h in TABLES[table_name]["headers"]})
        except Exception as e:
            messagebox.showerror("File Error", f"Unable to write {TABLES[table_name]['file']}: {e}")

    # ---------------- Action message helpers ----------------
    def notify_view(self, message: str, timeout: int = 3000):
        try:
            if self._view_notify_label and self._view_notify_label.winfo_exists():
                self._view_notify_label.configure(text=message, text_color="#86efac")
                def _clear():
                    try:
                        if self._view_notify_label and self._view_notify_label.winfo_exists():
                            self._view_notify_label.configure(text="")
                    except Exception:
                        pass
                self.after(timeout, _clear)
        except Exception:
            pass

    def _set_tree_action_message(self, tree: ttk.Treeview, message: str, success: bool = True, timeout: int = 4000):
        try:
            lbl = getattr(tree, "_action_label", None)
            color = "#86efac" if success else "#fca5a5"
            if lbl and lbl.winfo_exists():
                lbl.configure(text=message, text_color=color)
                def _clear():
                    try:
                        if lbl and lbl.winfo_exists():
                            lbl.configure(text="")
                    except Exception:
                        pass
                self.after(timeout, _clear)
            else:
                try:
                    self.status.configure(text=message, text_color=color)
                    self.after(timeout, lambda: self.status.configure(text="Ready • F8 Quick Add • Ctrl+F Search", text_color="#fca5a5"))
                except Exception:
                    pass
        except Exception:
            pass

    # ---------------- Quick Add ----------------
    def quick_add(self):
        win = ctk.CTkToplevel(self)
        win.title("Quick Add")
        win.grab_set()
        self._register_popup(win)
        win.configure(fg_color="#050505")

        header = ctk.CTkLabel(win, text="Quick Add Player", text_color="#f1c40f",
                              font=ctk.CTkFont(size=14, weight="bold"))
        header.pack(pady=(10, 6), padx=12)

        table_var = tk.StringVar(value="Clan")
        table_combo = ctk.CTkComboBox(win, values=list(TABLES.keys()), variable=table_var, width=220)
        table_combo.pack(pady=(0, 8), padx=12)
        table_combo.configure(command=lambda v: table_var.set(v))

        scroll = ctk.CTkScrollableFrame(win, height=300, fg_color="#0b0b0b")
        scroll.pack(fill="both", expand=True, padx=12, pady=8)

        entries: Dict[str, object] = {}
        combo_defaults: Dict[str, str] = {}

        def create_fields():
            for w in scroll.winfo_children():
                w.destroy()
            entries.clear()
            combo_defaults.clear()

            ctk.CTkLabel(scroll, text="Player Tag *", text_color="#fecaca").pack(anchor="w", pady=(6, 4))
            tagf = ctk.CTkFrame(scroll, fg_color="transparent")
            tagf.pack(fill="x", pady=(0, 6))
            entries["Tag"] = ctk.CTkEntry(tagf, width=300, height=30)
            entries["Tag"].pack(side="left", padx=(0, 8))
            ctk.CTkButton(tagf, text="📋 Paste", width=80, height=30,
                          command=lambda: entries["Tag"].insert(0, pyperclip.paste() or "")).pack(side="left")

            ctk.CTkLabel(scroll, text="In-game Name", text_color="#fecaca").pack(anchor="w", pady=(8, 4))
            entries["Name"] = ctk.CTkEntry(scroll, width=420, height=30)
            entries["Name"].pack(pady=4)

            sel = table_var.get()
            if sel == "Clan":
                for label, key, vals, default in [
                    ("State", "State", INDIAN_STATES, "Unknown"),
                    ("Map", "Map", MAPS, "Map 1"),
                    ("Role", "Role", ["Member", "Elder", "Co-Leader", "Under Check"], "Member"),
                    ("Status", "Status", ["Active", "On Leave"], "Active")
                ]:
                    ctk.CTkLabel(scroll, text=label, text_color="#fecaca").pack(anchor="w", pady=(8, 4))
                    entries[key] = ctk.CTkComboBox(scroll, values=vals, width=420)
                    entries[key].set(default)
                    entries[key].pack(pady=4)
                    combo_defaults[key] = default
                for f in ["Discord ID", "Note"]:
                    ctk.CTkLabel(scroll, text=f, text_color="#fecaca").pack(anchor="w", pady=(8, 4))
                    entries[f] = ctk.CTkEntry(scroll, width=420, height=30)
                    entries[f].pack(pady=4)
            else:
                for f in ["Reason", "Note", "Proof"]:
                    ctk.CTkLabel(scroll, text=f, text_color="#fecaca").pack(anchor="w", pady=(8, 4))
                    entries[f] = ctk.CTkEntry(scroll, width=420, height=30)
                    entries[f].pack(pady=4)

            try:
                entries["Tag"].focus_set()
                entries["Tag"].select_range(0, "end")
            except Exception:
                pass

        table_var.trace_add("write", lambda *a: create_fields())
        create_fields()

        keep_open_var = tk.BooleanVar(value=False)
        chk_frame = ctk.CTkFrame(win, fg_color="transparent")
        chk_frame.pack(fill="x", padx=12)
        ctk.CTkCheckBox(chk_frame, text="Keep Quick Add open after save",
                        variable=keep_open_var, onvalue=True, offvalue=False).pack(anchor="w", pady=(4, 0))

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(8, 10), padx=12)
        save_btn = ctk.CTkButton(btn_frame, text="💀 SAVE (Enter)", height=36, fg_color="#991b1b",
                                 command=lambda: self.save_quick(win, entries, table_var.get(), keep_open_var.get(), combo_defaults))
        save_btn.pack(side="left", padx=(0, 8))
        back_btn = ctk.CTkButton(btn_frame, text="← Back", height=36, fg_color="#334155",
                                 command=lambda: self._unregister_and_close(win))
        back_btn.pack(side="left")

        win.bind("<Return>", lambda e: self.save_quick(win, entries, table_var.get(), keep_open_var.get(), combo_defaults))
        win.bind("<Escape>", lambda e: self._unregister_and_close(win))

        self._autosize_and_center(win, padding=(20, 20), min_size=(420, 320), center_on="screen")

    def save_quick(self, win, entries: Dict[str, object], table_name: str, keep_open: bool = False, combo_defaults: Dict[str, str] = None):
        tag_widget = entries.get("Tag")
        if not tag_widget or not tag_widget.get().strip():
            messagebox.showerror("Error", "Player Tag is mandatory!")
            return
        tag_val = tag_widget.get().strip()
        name_val = entries.get("Name").get().strip() if "Name" in entries else ""

        data = {h: (entries.get(h).get().strip() if h in entries else "") for h in TABLES[table_name]["headers"]}
        data["Tag"] = tag_val
        data["Name"] = name_val

        token = tag_val.lower()
        if token:
            for tbl, row in self.load_all_rows():
                existing_tag = (row.get("Tag") or "").strip().lower()
                if existing_tag == token:
                    details_lines = [f"{h}: {row.get(h,'')}" for h in TABLES[tbl]["headers"]]
                    details = "\n".join(details_lines)
                    messagebox.showerror("Duplicate Tag",
                                         f"Player Tag '{tag_val}' already exists in table '{tbl}'.\n\nExisting record details:\n\n{details}")
                    return

        self.ensure_csv(table_name)
        try:
            with open(TABLES[table_name]["file"], "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=TABLES[table_name]["headers"])
                writer.writerow({h: data.get(h, "") for h in TABLES[table_name]["headers"]})
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
            return

        self.status.configure(text=f"✅ Saved {tag_val} to {table_name}", text_color="#86efac")
        self.after(3000, lambda: self.status.configure(text="Ready • F8 Quick Add • Ctrl+F Search", text_color="#fca5a5"))

        if keep_open:
            for h, widget in entries.items():
                try:
                    if isinstance(widget, ctk.CTkEntry):
                        widget.delete(0, "end")
                    elif isinstance(widget, ctk.CTkComboBox):
                        if combo_defaults and h in combo_defaults:
                            widget.set(combo_defaults[h])
                        else:
                            try:
                                vals = widget._values if hasattr(widget, "_values") else None
                                if vals and len(vals) > 0:
                                    widget.set(vals[0])
                                else:
                                    widget.set("")
                            except Exception:
                                widget.set("")
                except Exception:
                    pass
            try:
                entries["Tag"].focus_set()
                entries["Tag"].select_range(0, "end")
            except Exception:
                pass
            return

        self._unregister_and_close(win)

    # ---------------- View & Manage ----------------
    def show_view_window(self):
        win = ctk.CTkToplevel(self)
        win.title("View & Manage")
        win.geometry("980x560")
        win.grab_set()
        self._register_popup(win)
        win.configure(fg_color="#050505")

        header = ctk.CTkFrame(win, fg_color="transparent")
        header.pack(fill="x", pady=(6, 8), padx=12)

        ctk.CTkLabel(header, text="Table:", text_color="#f1c40f").pack(side="left", padx=(6, 8))
        table_var = tk.StringVar(value="Clan")
        table_combo = ctk.CTkComboBox(header, values=["All"] + list(TABLES.keys()), variable=table_var, width=160)
        table_combo.pack(side="left", padx=(0, 12))

        self._view_notify_label = ctk.CTkLabel(header, text="", text_color="#86efac")
        self._view_notify_label.pack(side="left", padx=(8, 12))

        ctk.CTkLabel(header, text="Move To:", text_color="#f1c40f").pack(side="left", padx=(6, 8))
        move_target_var = tk.StringVar()
        move_target_combo = ctk.CTkComboBox(header, values=[], variable=move_target_var, width=160)
        move_target_combo.pack(side="left", padx=(0, 8))
        move_btn = ctk.CTkButton(header, text="Move Selected", fg_color="#854d0e",
                                 command=lambda: self.move_selected_to(tree, table_var.get(), move_target_var.get()))
        move_btn.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(header, text="Filter (Tag/Name):", text_color="#f1c40f").pack(side="left", padx=(12, 6))
        filter_var = tk.StringVar()
        filter_entry = ctk.CTkEntry(header, textvariable=filter_var, width=220)
        filter_entry.pack(side="left", padx=(0, 8))

        paging_frame = ctk.CTkFrame(header, fg_color="transparent")
        paging_frame.pack(side="right", padx=(6, 0))
        prev_btn = ctk.CTkButton(paging_frame, text="◀ Prev", width=80, fg_color="#334155")
        next_btn = ctk.CTkButton(paging_frame, text="Next ▶", width=80, fg_color="#334155")
        page_label = ctk.CTkLabel(paging_frame, text="Page 1 / 1", text_color="#fca5a5")
        prev_btn.pack(side="left", padx=(6, 4))
        page_label.pack(side="left", padx=(4, 4))
        next_btn.pack(side="left", padx=(4, 6))

        tree_frame = ctk.CTkFrame(win)
        tree_frame.pack(fill="both", expand=True, padx=12, pady=8)
        tree = ttk.Treeview(tree_frame, show="headings", style="Custom.Treeview", selectmode="extended")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        # Tag styles including Under Check (red)
        tree.tag_configure("role_member", foreground="#16a34a")
        tree.tag_configure("role_elder", foreground="#0ea5e9")
        tree.tag_configure("role_coleader", foreground="#f59e0b")
        tree.tag_configure("role_undercheck", foreground="#dc2626")  # red for Under Check
        tree.tag_configure("oddrow", background="#0b0b0b")
        tree.tag_configure("evenrow", background="#071018")
        tree.tag_configure("blacklisted_row", foreground="#ffffff")
        tree.tag_configure("removed_row", foreground="#ffffff")
        tree.tag_configure("match", foreground="#f59e0b")

        control = ctk.CTkFrame(win, fg_color="transparent")
        control.pack(pady=6)
        edit_btn = ctk.CTkButton(control, text="✏️ Edit", fg_color="#eab308", text_color="black",
                                 command=lambda: self.edit_entry(tree, table_var.get()))
        edit_btn.pack(side="left", padx=6)
        del_btn = ctk.CTkButton(control, text="☠️ Delete", fg_color="#991b1b",
                                command=lambda: self.delete_entry(tree, table_var.get()))
        del_btn.pack(side="left", padx=6)
        ctk.CTkButton(control, text="↩️ Undo Last", fg_color="#3b82f6",
                      command=lambda: self.undo_last_action(tree, table_var.get())).pack(side="left", padx=6)
        ctk.CTkButton(control, text="← Back", fg_color="#334155",
                      command=lambda: self._close_view_and_unregister(win)).pack(side="left", padx=6)

        footer = ctk.CTkFrame(win, fg_color="transparent")
        footer.pack(fill="x", padx=12, pady=(4,8))
        action_label = ctk.CTkLabel(footer, text="", text_color="#86efac", anchor="w")
        action_label.pack(side="left", padx=(6,6))
        tree._action_label = action_label

        tree.bind("<Double-1>", lambda e: self._on_tree_double_click(e, tree, table_var.get()))

        page_var = tk.IntVar(value=1)

        def update_page_label():
            total = self._count_rows_for_table(table_var.get(), filter_var.get())
            max_page = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
            if page_var.get() > max_page:
                page_var.set(max_page)
            page_label.configure(text=f"Page {page_var.get()} / {max_page}")

        def prev_page():
            if page_var.get() > 1:
                page_var.set(page_var.get() - 1)
                update_page_label()
                self.refresh_table(tree, table_var.get(), filter_var.get(), page_var.get())

        def next_page():
            total = self._count_rows_for_table(table_var.get(), filter_var.get())
            max_page = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
            if page_var.get() < max_page:
                page_var.set(page_var.get() + 1)
                update_page_label()
                self.refresh_table(tree, table_var.get(), filter_var.get(), page_var.get())

        prev_btn.configure(command=prev_page)
        next_btn.configure(command=next_page)

        def on_table_change(*args):
            current = table_var.get()
            targets = [t for t in TABLES.keys() if t != current]
            if current == "All":
                targets = list(TABLES.keys())
            move_target_combo.configure(values=targets)
            if targets:
                if move_target_var.get() not in targets:
                    move_target_var.set(targets[0])
            else:
                move_target_var.set("")
            if current == "All":
                edit_btn.configure(state="disabled")
                del_btn.configure(state="disabled")
            else:
                edit_btn.configure(state="normal")
                del_btn.configure(state="normal")
            page_var.set(1)
            update_page_label()
            self.refresh_table(tree, current, filter_var.get(), page_var.get())

        table_combo.configure(command=lambda v: table_var.set(v))
        table_var.trace_add("write", on_table_change)
        filter_var.trace_add("write", lambda *a: (page_var.set(1), update_page_label(), self.refresh_table(tree, table_var.get(), filter_var.get(), page_var.get())))

        table_combo.set(table_var.get())
        update_page_label()
        on_table_change()

        tree._page_var = page_var
        tree._current_page = 1

        self._last_view_window = win
        self._last_view_tree = tree
        self._last_view_table_var = table_var
        self._last_view_filter_var = filter_var
        self._last_view_page_var = page_var

        self._autosize_and_center(win, padding=(20, 20), min_size=(760,420), center_on="screen")
        return win

    def open_record_in_view(self, table: str, tag: str):
        if not (self._last_view_window and self._last_view_window.winfo_exists()):
            self.show_view_window()

        tree = self._last_view_tree
        table_var = self._last_view_table_var
        filter_var = self._last_view_filter_var
        page_var = self._last_view_page_var

        if not (tree and table_var and filter_var and page_var):
            return

        table_var.set(table)
        filter_var.set(tag)
        self.refresh_table(tree, table, tag, page_var.get())

        for iid in tree.get_children():
            vals = tree.item(iid).get("values", [])
            if vals and len(vals) > 0 and str(vals[0]).strip() == str(tag).strip():
                tree.selection_set(iid)
                tree.focus(iid)
                tree.see(iid)
                self.edit_entry(tree, table)
                return

        self._set_tree_action_message(tree, f"Record '{tag}' not found in {table}", success=False)

    def _close_view_and_unregister(self, win):
        try:
            if self._view_notify_label:
                self._view_notify_label.configure(text="")
        except Exception:
            pass
        self._unregister_and_close(win)
        if self._last_view_window is win:
            self._last_view_window = None
            self._last_view_tree = None
            self._last_view_table_var = None
            self._last_view_filter_var = None
            self._last_view_page_var = None
        self._view_notify_label = None

    def _count_rows_for_table(self, table_name: str, filter_text: str = "") -> int:
        ft = (filter_text or "").strip().lower()
        if table_name == "All":
            tag_index = {}
            for tbl in TABLES.keys():
                rows = self.load_table(tbl)
                for r in rows:
                    tag = (r.get("Tag") or "").strip()
                    if not tag:
                        continue
                    if ft:
                        if ft not in tag.lower() and ft not in (r.get("Name") or "").lower():
                            continue
                    tag_index[tag] = True
            return len(tag_index)
        else:
            rows = self.load_table(table_name)
            if ft:
                rows = [r for r in rows if ft in (r.get("Tag", "").lower()) or ft in (r.get("Name", "").lower())]
            return len(rows)

    def refresh_table(self, tree: ttk.Treeview, table_name: str, filter_text: str = "", page: int = 1):
        for item in tree.get_children():
            tree.delete(item)

        def _role_tag_for_row(r):
            role = (r.get("Role", "") or "").strip().lower()
            if role == "member":
                return "role_member"
            if role == "elder":
                return "role_elder"
            if role in ("co-leader", "coleader", "co leader"):
                return "role_coleader"
            if role == "under check" or role == "undercheck":
                return "role_undercheck"
            return ""

        ft = (filter_text or "").strip().lower()

        if table_name == "All":
            all_headers = []
            seen = set()
            for h in TABLES["Clan"]["headers"]:
                all_headers.append(h); seen.add(h)
            for tbl in ["Blacklisted", "Removed"]:
                for h in TABLES[tbl]["headers"]:
                    if h not in seen:
                        all_headers.append(h); seen.add(h)
            final_headers = all_headers + ["Sources"]

            tag_index: Dict[str, Dict] = {}
            tag_sources: Dict[str, List[str]] = {}
            for tbl in ["Clan", "Blacklisted", "Removed"]:
                rows = self.load_table(tbl)
                for r in rows:
                    tag = (r.get("Tag") or "").strip()
                    if not tag:
                        continue
                    if ft:
                        if ft not in tag.lower() and ft not in (r.get("Name") or "").lower():
                            continue
                    if tag not in tag_index:
                        tag_index[tag] = {h: "" for h in all_headers}
                        tag_index[tag]["Tag"] = tag
                        tag_sources[tag] = []
                    for h in TABLES[tbl]["headers"]:
                        val = (r.get(h) or "").strip()
                        if val and not tag_index[tag].get(h):
                            tag_index[tag][h] = val
                    if tbl not in tag_sources[tag]:
                        tag_sources[tag].append(tbl)

            filtered_tags = sorted(list(tag_index.keys()))
            total = len(filtered_tags)
            max_page = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
            page = max(1, min(page, max_page))
            start = (page - 1) * PAGE_SIZE
            end = start + PAGE_SIZE
            page_tags = filtered_tags[start:end]

            tree["columns"] = final_headers
            for col in final_headers:
                tree.heading(col, text=col)
                tree.column(col, width=140, anchor="w", stretch=True)

            for i, tg in enumerate(page_tags):
                row = tag_index[tg]
                sources = ", ".join(tag_sources.get(tg, []))
                values = [row.get(h, "") for h in all_headers] + [sources]

                matched = False
                if ft:
                    if ft in (row.get("Tag", "").lower()) or ft in (row.get("Name", "").lower()):
                        matched = True

                base_tags = []
                if matched:
                    base_tags.append("match")
                    if "Blacklisted" in tag_sources.get(tg, []):
                        base_tags.append("blacklisted_row")
                    if "Removed" in tag_sources.get(tg, []):
                        base_tags.append("removed_row")
                    if row.get("Role", "") and "Clan" in tag_sources.get(tg, []):
                        base_tags.append(_role_tag_for_row(row))
                else:
                    if "Blacklisted" in tag_sources.get(tg, []):
                        base_tags.append("blacklisted_row")
                    elif "Removed" in tag_sources.get(tg, []):
                        base_tags.append("removed_row")
                    elif row.get("Role", ""):
                        base_tags.append(_role_tag_for_row(row))

                row_tag = "evenrow" if i % 2 == 0 else "oddrow"
                tags = tuple([t for t in base_tags if t]) + (row_tag,)
                tree.insert("", "end", values=values, tags=tags)

            try:
                tree._current_page = page
                if hasattr(tree, "_page_var") and isinstance(tree._page_var, tk.IntVar):
                    tree._page_var.set(page)
            except Exception:
                pass
            return

        if table_name not in TABLES:
            return
        self.ensure_csv(table_name)
        headers = TABLES[table_name]["headers"]
        rows = self.load_table(table_name)

        if ft:
            rows = [r for r in rows if ft in (r.get("Tag", "").lower()) or ft in (r.get("Name", "").lower())]

        total = len(rows)
        max_page = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        page = max(1, min(page, max_page))
        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        page_rows = rows[start:end]

        tree["columns"] = headers
        for col in headers:
            tree.heading(col, text=col)
            tree.column(col, width=140, anchor="w", stretch=True)

        for i, row in enumerate(page_rows):
            matched = False
            if ft:
                if ft in (row.get("Tag", "").lower()) or ft in (row.get("Name", "").lower()):
                    matched = True

            base_tags = []
            if matched:
                base_tags.append("match")
                if table_name == "Blacklisted":
                    base_tags.append("blacklisted_row")
                if table_name == "Removed":
                    base_tags.append("removed_row")
                if table_name == "Clan" and row.get("Role", ""):
                    base_tags.append(_role_tag_for_row(row))
            else:
                if table_name == "Blacklisted":
                    base_tags.append("blacklisted_row")
                if table_name == "Removed":
                    base_tags.append("removed_row")
                if table_name == "Clan" and row.get("Role", ""):
                    base_tags.append(_role_tag_for_row(row))

            row_tag = "evenrow" if i % 2 == 0 else "oddrow"
            tags = tuple([t for t in base_tags if t]) + (row_tag,)
            values = [row.get(h, "") for h in headers]
            tree.insert("", "end", values=values, tags=tags)

        try:
            tree._current_page = page
            if hasattr(tree, "_page_var") and isinstance(tree._page_var, tk.IntVar):
                tree._page_var.set(page)
        except Exception:
            pass

    # ---------------- Note / Edit / Delete / Move / Undo ----------------
    def _on_tree_double_click(self, event, tree: ttk.Treeview, current_table: str):
        row_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)
        if not row_id:
            return
        try:
            col_index = int(col_id.replace("#", "")) - 1
        except Exception:
            col_index = None
        vals = tree.item(row_id).get("values", [])
        if current_table != "All":
            headers = TABLES.get(current_table, {}).get("headers", [])
            if col_index is not None and 0 <= col_index < len(headers) and headers[col_index] == "Note":
                row_dict = {h: (vals[i] if i < len(vals) else "") for i, h in enumerate(headers)}
                if "Tag" not in row_dict and len(vals) > 0:
                    row_dict["Tag"] = vals[0]
                if "Name" not in row_dict and len(vals) > 1:
                    row_dict["Name"] = vals[1]
                self.show_note_popup(current_table, row_dict, parent_tree=tree, parent_iid=row_id)
                return
        if current_table != "All":
            self.edit_entry(tree, current_table)

    def show_note_popup(self, table_name: str, row: Dict[str, str], parent_tree: Optional[ttk.Treeview] = None, parent_iid: Optional[str] = None):
        note_text = (row.get("Note") or "").strip()
        win = ctk.CTkToplevel(self)
        win.title("Note")
        win.grab_set()
        self._register_popup(win)
        win.configure(fg_color="#050505")
        frm = ctk.CTkFrame(win, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=10, pady=10)
        lbl = ctk.CTkLabel(frm, text=f"Note for {row.get('Tag','')}", text_color="#f1c40f")
        lbl.pack(anchor="w", pady=(4,6))
        txt_frame = tk.Frame(frm, bg="#0b0b0b")
        txt_frame.pack(fill="both", expand=True, pady=(0,8))
        txt = tk.Text(txt_frame, height=6, wrap="word", bg="#0b0b0b", fg="#e5e7eb", insertbackground="#e5e7eb", relief="flat", bd=0)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", note_text)
        txt.configure(state="disabled")
        btn_frame = ctk.CTkFrame(frm, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(6,2))
        def enable_edit():
            try:
                txt.configure(state="normal")
                txt.focus_set()
            except Exception:
                pass
        def erase_note():
            if messagebox.askyesno("Erase Note", "Erase the note content?"):
                try:
                    txt.configure(state="normal")
                    txt.delete("1.0", "end")
                except Exception:
                    pass
        def save_note():
            new_note = txt.get("1.0", "end").rstrip("\n")
            headers = TABLES.get(table_name, {}).get("headers", [])
            if "Tag" not in headers:
                messagebox.showerror("Save", "Cannot save: table missing Tag header.")
                return
            tag_val = (row.get("Tag") or "").strip()
            rows = list(self.load_table(table_name))
            updated = False
            for i, r in enumerate(rows):
                if (r.get("Tag") or "").strip() == tag_val:
                    for h in headers:
                        rows[i][h] = rows[i].get(h, "")
                    rows[i]["Note"] = new_note
                    updated = True
                    break
            if not updated:
                new_row = {h: "" for h in headers}
                new_row["Tag"] = tag_val
                new_row["Name"] = row.get("Name","")
                new_row["Note"] = new_note
                rows.append(new_row)
            try:
                self.write_table(table_name, rows)
                self.notify_view(f"Note saved for {tag_val}")
                if parent_tree and parent_tree.winfo_exists():
                    current_page = getattr(parent_tree, "_current_page", 1)
                    self.refresh_table(parent_tree, table_name, "", current_page)
                    self._set_tree_action_message(parent_tree, f"Note saved for {tag_val}", success=True)
            except Exception as e:
                if parent_tree and parent_tree.winfo_exists():
                    self._set_tree_action_message(parent_tree, f"Failed to save note: {e}", success=False)
            self._unregister_and_close(win)
        ctk.CTkButton(btn_frame, text="Edit", fg_color="#eab308", command=enable_edit).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Erase", fg_color="#991b1b", command=erase_note).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Save", fg_color="#16a34a", command=save_note).pack(side="left", padx=6)

    def edit_entry(self, tree: ttk.Treeview, current_table: str):
        if current_table == "All":
            messagebox.showinfo("Edit", "Switch to a specific table to edit entries.")
            return
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Edit", "Select a row to edit.")
            return
        iid = sel[0]
        vals = tree.item(iid).get("values", [])
        headers = TABLES.get(current_table, {}).get("headers", [])
        row_data = {h: (vals[i] if i < len(vals) else "") for i, h in enumerate(headers)}
        win = ctk.CTkToplevel(self)
        win.title(f"Edit {current_table}")
        win.grab_set()
        self._register_popup(win)
        frm = ctk.CTkFrame(win, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=10, pady=10)
        entries = {}
        for h in headers:
            ctk.CTkLabel(frm, text=h, text_color="#fecaca").pack(anchor="w", pady=(6,2))
            if current_table == "Clan" and h in ("State", "Map", "Role", "Status"):
                vals = INDIAN_STATES if h == "State" else (MAPS if h == "Map" else (["Member","Elder","Co-Leader","Under Check"] if h == "Role" else ["Active","On Leave"]))
                cb = ctk.CTkComboBox(frm, values=vals, width=420)
                cb.pack(pady=2)
                cb.set(row_data.get(h, vals[0] if vals else ""))
                entries[h] = cb
            else:
                e = ctk.CTkEntry(frm, width=420, height=30)
                e.pack(pady=2)
                e.insert(0, row_data.get(h, ""))
                entries[h] = e
        btn_frame = ctk.CTkFrame(frm, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(8,2))
        def on_save():
            tag_val = entries.get("Tag").get().strip() if "Tag" in entries else ""
            if not tag_val:
                messagebox.showerror("Error", "Tag is mandatory.")
                return
            rows = list(self.load_table(current_table))
            updated = False
            for i, r in enumerate(rows):
                if (r.get("Tag") or "").strip() == tag_val:
                    for h in headers:
                        widget = entries.get(h)
                        if isinstance(widget, ctk.CTkComboBox):
                            rows[i][h] = widget.get().strip()
                        else:
                            rows[i][h] = widget.get().strip()
                    updated = True
                    break
            if not updated:
                new_row = {}
                for h in headers:
                    widget = entries.get(h)
                    new_row[h] = widget.get().strip() if widget is not None else ""
                rows.append(new_row)
            try:
                self.write_table(current_table, rows)
                self._undo_stack.append({"action": "edit", "table": current_table, "tag": tag_val})
                self._set_tree_action_message(tree, f"Updated {tag_val} in {current_table}", success=True)
                current_page = getattr(tree, "_current_page", 1)
                self.refresh_table(tree, current_table, "", current_page)
            except Exception as e:
                self._set_tree_action_message(tree, f"Failed to save edit: {e}", success=False)
            self._unregister_and_close(win)
        ctk.CTkButton(btn_frame, text="Save", fg_color="#16a34a", command=on_save).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#334155", command=lambda: self._unregister_and_close(win)).pack(side="left", padx=6)

    def delete_entry(self, tree: ttk.Treeview, current_table: str):
        if current_table == "All":
            messagebox.showinfo("Delete", "Switch to a specific table to delete entries.")
            return
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Delete", "Select one or more rows to delete.")
            return
        headers = TABLES.get(current_table, {}).get("headers", [])
        rows = list(self.load_table(current_table))
        deleted = []
        for iid in sel:
            vals = tree.item(iid).get("values", [])
            tag_val = vals[0] if len(vals) > 0 else ""
            new_rows = []
            for r in rows:
                if (r.get("Tag") or "").strip() == (tag_val or "").strip():
                    deleted.append(r.copy())
                else:
                    new_rows.append(r)
            rows = new_rows
        try:
            self.write_table(current_table, rows)
            self._undo_stack.append({"action": "delete", "table": current_table, "rows": deleted})
            self._set_tree_action_message(tree, f"Deleted {len(deleted)} rows from {current_table}", success=True)
            current_page = getattr(tree, "_current_page", 1)
            self.refresh_table(tree, current_table, "", current_page)
        except Exception as e:
            self._set_tree_action_message(tree, f"Failed to delete: {e}", success=False)

    def move_selected_to(self, tree: ttk.Treeview, from_table: str, to_table: str):
        if not to_table or to_table == from_table:
            self._set_tree_action_message(tree, "Select a different target table.", success=False)
            return
        sel = tree.selection()
        if not sel:
            self._set_tree_action_message(tree, "Select rows to move.", success=False)
            return
        src_rows = list(self.load_table(from_table))
        moved = []
        remaining = []
        for iid in sel:
            vals = tree.item(iid).get("values", [])
            tag_val = vals[0] if len(vals) > 0 else ""
            for r in src_rows:
                if (r.get("Tag") or "").strip() == (tag_val or "").strip():
                    moved.append(r.copy())
                    break
        if not moved:
            self._set_tree_action_message(tree, "No matching rows found to move.", success=False)
            return
        for r in src_rows:
            if any((r.get("Tag") or "").strip() == (m.get("Tag") or "").strip() for m in moved):
                continue
            remaining.append(r)
        dest_rows = list(self.load_table(to_table))
        dest_tags = {(r.get("Tag") or "").strip().lower() for r in dest_rows}
        appended = 0
        for m in moved:
            if (m.get("Tag") or "").strip().lower() not in dest_tags:
                dest_headers = TABLES[to_table]["headers"]
                new_row = {h: m.get(h, "") for h in dest_headers}
                if "Tag" in dest_headers and not new_row.get("Tag"):
                    new_row["Tag"] = m.get("Tag", "")
                if "Name" in dest_headers and not new_row.get("Name"):
                    new_row["Name"] = m.get("Name", "")
                dest_rows.append(new_row)
                appended += 1
        try:
            self.write_table(from_table, remaining)
            self.write_table(to_table, dest_rows)
            self._undo_stack.append({"action": "move", "from": from_table, "to": to_table, "rows": moved})
            self._set_tree_action_message(tree, f"Moved {appended} rows from {from_table} → {to_table}", success=True)
            current_page = getattr(tree, "_current_page", 1)
            if getattr(tree, "columns", None) and "Table" in tree["columns"]:
                self.refresh_table(tree, "All", "", current_page)
            else:
                self.refresh_table(tree, from_table, "", current_page)
        except Exception as e:
            self._set_tree_action_message(tree, f"Failed to move rows: {e}", success=False)

    def undo_last_action(self, tree: ttk.Treeview, current_table: str):
        if not self._undo_stack:
            messagebox.showinfo("Undo", "Nothing to undo.")
            return
        last = self._undo_stack.pop()
        action = last.get("action")
        try:
            if action == "delete":
                table = last.get("table")
                rows = last.get("rows", [])
                existing = list(self.load_table(table))
                existing.extend(rows)
                self.write_table(table, existing)
                self._set_tree_action_message(tree, f"Restored {len(rows)} rows to {table}", success=True)
            elif action == "move":
                from_table = last.get("from")
                to_table = last.get("to")
                rows = last.get("rows", [])
                to_rows = [r for r in self.load_table(to_table) if (r.get("Tag") or "").strip().lower() not in {(m.get("Tag") or "").strip().lower() for m in rows}]
                from_rows = list(self.load_table(from_table))
                from_rows.extend(rows)
                self.write_table(to_table, to_rows)
                self.write_table(from_table, from_rows)
                self._set_tree_action_message(tree, f"Moved back {len(rows)} rows to {from_table}", success=True)
            elif action == "edit":
                messagebox.showinfo("Undo", "Edit undo not available for this action.")
                return
            else:
                messagebox.showinfo("Undo", "Unknown undo action.")
                return
            current_page = getattr(tree, "_current_page", 1)
            if getattr(tree, "columns", None) and "Table" in tree["columns"]:
                self.refresh_table(tree, "All", "", current_page)
            else:
                self.refresh_table(tree, current_table, "", current_page)
        except Exception as e:
            messagebox.showerror("Undo Error", f"Failed to undo: {e}")
            self._set_tree_action_message(tree, f"Undo failed: {e}", success=False)

    # ---------------- Monster Hunt Module ----------------
    def show_monster_hunt(self):
        win = ctk.CTkToplevel(self)
        win.title("Monster Hunt")
        win.geometry("920x560")
        win.grab_set()
        self._register_popup(win)
        win.configure(fg_color="#050505")

        header = ctk.CTkFrame(win, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(8,6))
        today = datetime.date.today()
        month_var = tk.IntVar(value=today.month)
        year_var = tk.IntVar(value=today.year)

        def prev_month():
            m = month_var.get() - 1
            y = year_var.get()
            if m < 1:
                m = 12
                y -= 1
            cur = datetime.date(today.year, today.month, 1)
            candidate = datetime.date(y, m, 1)
            if candidate < (cur - datetime.timedelta(days=31)):
                return
            month_var.set(m); year_var.set(y); render_calendar()

        def next_month():
            m = month_var.get() + 1
            y = year_var.get()
            if m > 12:
                m = 1
                y += 1
            cur = datetime.date(today.year, today.month, 1)
            candidate = datetime.date(y, m, 1)
            if candidate > cur:
                return
            month_var.set(m); year_var.set(y); render_calendar()

        ctk.CTkButton(header, text="◀", width=36, command=prev_month).pack(side="left", padx=(6,6))
        month_label = ctk.CTkLabel(header, text=f"{calendar.month_name[month_var.get()]} {year_var.get()}", text_color="#f1c40f", font=ctk.CTkFont(size=14, weight="bold"))
        month_label.pack(side="left", padx=(6,12))
        ctk.CTkButton(header, text="▶", width=36, command=next_month).pack(side="left", padx=(6,6))

        main = ctk.CTkFrame(win, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=6)

        cal_container = ctk.CTkFrame(main, fg_color="transparent")
        cal_container.pack(side="left", fill="both", expand=True, padx=(12,6), pady=6)

        analysis_container = ctk.CTkFrame(main, fg_color="#0b0b0b", width=260, corner_radius=8)
        analysis_container.pack(side="right", fill="y", padx=(6,12), pady=6)
        analysis_container.pack_propagate(False)

        icon_lbl = ctk.CTkLabel(analysis_container, text="🧭", font=ctk.CTkFont(size=20))
        icon_lbl.pack(pady=(12,4))
        ctk.CTkLabel(analysis_container, text="Analysis", text_color="#f1c40f", font=ctk.CTkFont(size=14, weight="bold")).pack()
        ctk.CTkLabel(analysis_container, text="Choose how to visualize Monster Hunt data", text_color="#e5e7eb", wraplength=220).pack(pady=(6,8), padx=8)

        analysis_var = tk.StringVar(value="Participation per day")
        analysis_options = [
            "Participation per day",
            "Completed days count",
            "Average members",
            "List of days (detailed)"
        ]
        analysis_cb = ctk.CTkComboBox(analysis_container, values=analysis_options, variable=analysis_var, width=220)
        analysis_cb.pack(pady=(6,6))

        btn_row = ctk.CTkFrame(analysis_container, fg_color="transparent")
        btn_row.pack(pady=(6,6))
        ctk.CTkButton(btn_row, text="Run Analysis", fg_color="#1e3a8a", command=lambda: run_analysis()).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Export CSV", fg_color="#0f766e", command=lambda: export_analysis()).pack(side="left", padx=6)

        analysis_canvas_frame = tk.Frame(analysis_container, bg="#0b0b0b")
        analysis_canvas_frame.pack(fill="both", expand=True, padx=8, pady=(6,12))

        analysis_canvas = tk.Canvas(analysis_canvas_frame, bg="#0b0b0b", highlightthickness=0)
        analysis_canvas.pack(fill="both", expand=True)

        footer = ctk.CTkFrame(win, fg_color="transparent")
        footer.pack(fill="x", padx=12, pady=(4,8))
        action_label = ctk.CTkLabel(footer, text="", text_color="#86efac", anchor="w")
        action_label.pack(side="left", padx=(6,6))
        undo_btn = ctk.CTkButton(footer, text="↶ Undo Last Hunt Action", fg_color="#3b82f6", command=lambda: on_undo_monster())
        undo_btn.pack(side="right", padx=(6,6))

        def set_footer(msg: str, success: bool = True, timeout: int = 4000):
            color = "#86efac" if success else "#fca5a5"
            try:
                action_label.configure(text=msg, text_color=color)
                def _clear():
                    try:
                        action_label.configure(text="")
                    except Exception:
                        pass
                win.after(timeout, _clear)
            except Exception:
                pass

        day_cells: Dict[int, Dict[str, object]] = {}

        def render_calendar():
            monster_data = load_monster_csv()

            for w in cal_container.winfo_children():
                w.destroy()

            cal_box = tk.Frame(cal_container, bg="#ffffff", bd=0)
            cal_box.place(relx=0.5, rely=0.5, anchor="center")

            cal_inner = tk.Frame(cal_box, bg="#000000", width=560, height=520)
            cal_inner.pack_propagate(False)
            cal_inner.pack(padx=6, pady=6)

            month_label.configure(text=f"{calendar.month_name[month_var.get()]} {year_var.get()}")
            y = year_var.get(); m = month_var.get()
            month_days = calendar.monthrange(y, m)[1]
            first_weekday = calendar.monthrange(y, m)[0]  # 0=Mon

            header_row = tk.Frame(cal_inner, bg="#000000")
            header_row.pack(fill="x", pady=(6,4))
            weekdays = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
            for wd in weekdays:
                lbl = tk.Label(header_row, text=wd, bg="#000000", fg="#f1c40f", font=("TkDefaultFont", 9))
                lbl.pack(side="left", expand=True, fill="x", padx=2)

            grid_frame = tk.Frame(cal_inner, bg="#000000")
            grid_frame.pack(expand=True, fill="both", padx=6, pady=6)

            start = first_weekday
            day = 1
            day_cells.clear()
            cell_size = 64
            key = f"{y:04d}-{m:02d}"
            month_obj = monster_data.get(key, {})
            max_members = 0
            for drec in month_obj.values():
                try:
                    v = int(drec.get("members") or 0)
                    if v > max_members:
                        max_members = v
                except Exception:
                    pass
            for r in range(6):
                for c in range(7):
                    outer = tk.Frame(grid_frame, bg="#ffffff", bd=0)
                    outer.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
                    grid_frame.grid_columnconfigure(c, weight=1)
                    grid_frame.grid_rowconfigure(r, weight=1)
                    inner = tk.Frame(outer, bg="#000000", width=cell_size, height=cell_size)
                    inner.grid_propagate(False)
                    inner.pack(expand=True, fill="both")
                    cell_index = r * 7 + c
                    if cell_index >= start and day <= month_days:
                        day_num = day
                        lbl_date = tk.Label(inner, text=str(day_num), bg="#000000", fg="#f1c40f", anchor="nw", font=("TkDefaultFont", 9, "bold"))
                        lbl_date.pack(anchor="nw", padx=6, pady=(6,0))
                        info_lbl = tk.Label(inner, text="", bg="#000000", fg="#e5e7eb", anchor="w", justify="left", wraplength=cell_size-12, font=("TkDefaultFont", 8))
                        info_lbl.pack(anchor="w", padx=6, pady=(0,4))
                        done_lbl = tk.Label(inner, text="", bg="#000000", fg="#ff4d4d", anchor="ne", font=("TkDefaultFont", 12, "bold"))
                        done_lbl.place(relx=0.95, rely=0.05, anchor="ne")
                        menu = tk.Menu(inner, tearoff=0)
                        def make_edit(d=day_num):
                            return lambda: self._open_monster_day_popup(win, y, m, d, set_footer, render_calendar)
                        menu.add_command(label="Edit", command=make_edit())
                        def make_mark_done(d=day_num):
                            def _mark():
                                monster_data_local = load_monster_csv()
                                key_local = f"{y:04d}-{m:02d}"
                                month_local = monster_data_local.get(key_local, {})
                                before = month_local.get(str(d), {}).copy() if str(d) in month_local else {}
                                rec = month_local.get(str(d), {"members": "", "time": "", "map": MAPS_7_12[0], "server": SERVERS[0], "done": False})
                                rec["done"] = True
                                month_local[str(d)] = rec
                                monster_data_local[key_local] = month_local
                                append_monster_log("mark_done", y, m, d, before=before, after=rec)
                                save_monster_csv(monster_data_local)
                                set_footer(f"Marked done: {y}-{m:02d}-{d:02d}", success=True)
                                render_calendar()
                            return _mark
                        menu.add_command(label="Mark Done", command=make_mark_done())
                        def make_mark_undone(d=day_num):
                            def _unmark():
                                monster_data_local = load_monster_csv()
                                key_local = f"{y:04d}-{m:02d}"
                                month_local = monster_data_local.get(key_local, {})
                                before = month_local.get(str(d), {}).copy() if str(d) in month_local else {}
                                rec = month_local.get(str(d), {"members": "", "time": "", "map": MAPS_7_12[0], "server": SERVERS[0], "done": False})
                                rec["done"] = False
                                month_local[str(d)] = rec
                                monster_data_local[key_local] = month_local
                                append_monster_log("mark_undone", y, m, d, before=before, after=rec)
                                save_monster_csv(monster_data_local)
                                set_footer(f"Marked undone: {y}-{m:02d}-{d:02d}", success=True)
                                render_calendar()
                            return _unmark
                        menu.add_command(label="Mark Undone", command=make_mark_undone())
                        def make_clear(d=day_num):
                            def _clear():
                                monster_data_local = load_monster_csv()
                                key_local = f"{y:04d}-{m:02d}"
                                month_local = monster_data_local.get(key_local, {})
                                before = month_local.get(str(d), {}).copy() if str(d) in month_local else {}
                                if str(d) in month_local:
                                    month_local.pop(str(d), None)
                                monster_data_local[key_local] = month_local
                                append_monster_log("clear_day", y, m, d, before=before, after={})
                                save_monster_csv(monster_data_local)
                                set_footer(f"Cleared: {y}-{m:02d}-{d:02d}", success=True)
                                render_calendar()
                            return _clear
                        menu.add_command(label="Clear", command=make_clear())
                        def make_copy(d=day_num):
                            def _copy():
                                monster_data_local = load_monster_csv()
                                key_local = f"{y:04d}-{m:02d}"
                                rec = monster_data_local.get(key_local, {}).get(str(d), {})
                                txt = f"{y}-{m:02d}-{d:02d}: {rec.get('members','')} players; {rec.get('time','')}; {rec.get('map','')}; {rec.get('server','')}"
                                try:
                                    pyperclip.copy(txt)
                                    set_footer("Copied details to clipboard", success=True)
                                except Exception:
                                    set_footer("Failed to copy", success=False)
                            return _copy
                        menu.add_command(label="Copy details", command=make_copy())
                        def on_right_click(ev, m=menu):
                            try:
                                m.tk_popup(ev.x_root, ev.y_root)
                            finally:
                                m.grab_release()
                        inner.bind("<Button-3>", on_right_click)
                        lbl_date.bind("<Button-3>", on_right_click)
                        info_lbl.bind("<Button-3>", on_right_click)
                        done_lbl.bind("<Button-3>", on_right_click)
                        def on_cell_click(ev, d=day_num):
                            self._open_monster_day_popup(win, y, m, d, set_footer, render_calendar)
                        inner.bind("<Button-1>", on_cell_click)
                        lbl_date.bind("<Button-1>", on_cell_click)
                        info_lbl.bind("<Button-1>", on_cell_click)
                        done_lbl.bind("<Button-1>", on_cell_click)
                        day_cells[day_num] = {"info": info_lbl, "done": done_lbl, "frame": inner}
                        day += 1
                    else:
                        empty = tk.Label(inner, text="", bg="#000000")
                        empty.pack(expand=True, fill="both")

            key = f"{y:04d}-{m:02d}"
            month_obj = monster_data.get(key, {})
            max_members_local = max_members if max_members > 0 else 1
            for d in range(1, month_days+1):
                cell_info = day_cells.get(d)
                if not cell_info:
                    continue
                info_lbl = cell_info["info"]
                done_lbl = cell_info["done"]
                frame = cell_info["frame"]
                day_obj = month_obj.get(str(d), {})
                if day_obj:
                    members = day_obj.get("members", "")
                    time_s = day_obj.get("time", "")
                    map_s = day_obj.get("map", "")
                    server_s = day_obj.get("server", "")
                    parts = []
                    if members != "":
                        parts.append(f"{members} players")
                    if time_s:
                        parts.append(f"{time_s}")
                    if map_s:
                        parts.append(f"{map_s}")
                    if server_s:
                        parts.append(f"{server_s}")
                    info_lbl.configure(text="; ".join(parts))
                    if day_obj.get("done"):
                        done_lbl.configure(text="✖")
                        done_lbl.lift()
                    else:
                        done_lbl.configure(text="")
                    try:
                        mval = int(members) if members != "" else 0
                    except Exception:
                        mval = 0
                    color = heatmap_color_for_value(mval, max_members_local)
                    try:
                        frame.configure(bg=color)
                        info_lbl.configure(bg=color)
                        done_lbl.configure(bg=color)
                        for child in frame.winfo_children():
                            if isinstance(child, tk.Label) and child.cget("text").isdigit():
                                child.configure(fg=("#000000" if mval > max_members_local * 0.5 else "#f1c40f"), bg=color)
                    except Exception:
                        pass
                else:
                    info_lbl.configure(text="")
                    done_lbl.configure(text="")
                    try:
                        frame.configure(bg="#000000")
                        info_lbl.configure(bg="#000000")
                        done_lbl.configure(bg="#000000")
                        for child in frame.winfo_children():
                            if isinstance(child, tk.Label) and child.cget("text").isdigit():
                                child.configure(fg="#f1c40f", bg="#000000")
                    except Exception:
                        pass

            self._autosize_and_center(win, padding=(10,10), min_size=(820,520), center_on="screen")

        def run_analysis():
            analysis_canvas.delete("all")
            monster_data = load_monster_csv()
            y = year_var.get(); m = month_var.get()
            key = f"{y:04d}-{m:02d}"
            month_obj = monster_data.get(key, {})
            if not month_obj:
                analysis_canvas.create_text(130, 80, text="No data for this month", fill="#e5e7eb", font=("TkDefaultFont", 10))
                set_footer("Analysis: no data", success=False)
                return
            opt = analysis_var.get()
            if opt == "Participation per day":
                month_days = calendar.monthrange(y, m)[1]
                days = list(range(1, month_days+1))
                members = [int(month_obj.get(str(d), {}).get("members") or 0) for d in days]
                w = 220; h = 160; left = 20; bottom = h - 20
                analysis_canvas.config(width=240, height=220, bg="#0b0b0b")
                max_val = max(members) if members else 1
                max_val = max(1, max_val)
                bar_w = max(4, (w - left - 10) // max(1, len(days)))
                for i, d in enumerate(days):
                    x0 = left + i * bar_w + 2
                    x1 = x0 + bar_w - 2
                    val = members[i]
                    bar_h = int((val / max_val) * (h - 40))
                    y0 = bottom - bar_h
                    y1 = bottom
                    analysis_canvas.create_rectangle(x0, y0, x1, y1, fill="#16a34a", outline="#0f766e")
                    if i % max(1, len(days)//6) == 0:
                        analysis_canvas.create_text((x0 + x1) / 2, bottom + 8, text=str(d), fill="#e5e7eb", font=("TkDefaultFont", 7))
                set_footer("Analysis: Participation per day", success=True)
            elif opt == "Completed days count":
                done_count = sum(1 for v in month_obj.values() if v.get("done"))
                total = len(month_obj.keys())
                analysis_canvas.create_text(130, 80, text=f"Completed days: {done_count}\nRecorded days: {total}", fill="#e5e7eb", font=("TkDefaultFont", 10))
                set_footer(f"Analysis: {done_count} completed days", success=True)
            elif opt == "Average members":
                vals = [int(v.get("members") or 0) for v in month_obj.values() if v.get("members") != ""]
                if not vals:
                    analysis_canvas.create_text(130, 80, text="No members data", fill="#e5e7eb", font=("TkDefaultFont", 10))
                    set_footer("Analysis: no members data", success=False)
                else:
                    avg = sum(vals) / len(vals)
                    analysis_canvas.create_text(130, 80, text=f"Average members: {avg:.1f}", fill="#e5e7eb", font=("TkDefaultFont", 12))
                    set_footer(f"Analysis: average members {avg:.1f}", success=True)
            elif opt == "List of days (detailed)":
                lines = []
                for d in sorted(month_obj.keys(), key=lambda x: int(x)):
                    rec = month_obj[d]
                    parts = []
                    if rec.get("members") != "":
                        parts.append(f"{rec.get('members')} players")
                    if rec.get("time"):
                        parts.append(rec.get("time"))
                    if rec.get("map"):
                        parts.append(rec.get("map"))
                    if rec.get("server"):
                        parts.append(rec.get("server"))
                    done = "Done" if rec.get("done") else "Not done"
                    lines.append(f"{d}: {'; '.join(parts)} ({done})")
                text = "\n".join(lines)
                analysis_canvas.create_text(130, 80, text=text, fill="#e5e7eb", font=("TkDefaultFont", 8))
                set_footer("Analysis: detailed list", success=True)
            else:
                analysis_canvas.create_text(130, 80, text="Unknown analysis option", fill="#e5e7eb", font=("TkDefaultFont", 10))
                set_footer("Analysis: unknown option", success=False)

        def export_analysis():
            monster_data = load_monster_csv()
            y = year_var.get(); m = month_var.get()
            key = f"{y:04d}-{m:02d}"
            month_obj = monster_data.get(key, {})
            if not month_obj:
                set_footer("Export: no data to export", success=False)
                return
            try:
                default_name = f"monster_hunt_analysis_{key}.csv"
                path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name, filetypes=[("CSV files","*.csv")])
                if not path:
                    set_footer("Export cancelled", success=False)
                    return
                with open(path, "w", newline="", encoding="utf-8") as f:
                    fieldnames = ["month","day","members","time","map","server","done","note","proof"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for d in sorted(month_obj.keys(), key=lambda x: int(x)):
                        rec = month_obj[d]
                        writer.writerow({
                            "month": key,
                            "day": d,
                            "members": rec.get("members",""),
                            "time": rec.get("time",""),
                            "map": rec.get("map",""),
                            "server": rec.get("server",""),
                            "done": "1" if rec.get("done") else "0",
                            "note": rec.get("note",""),
                            "proof": rec.get("proof","")
                        })
                set_footer(f"Exported analysis to {os.path.basename(path)}", success=True)
            except Exception as e:
                set_footer(f"Export failed: {e}", success=False)

        def on_undo_monster():
            msg = undo_last_monster_action()
            if not msg:
                set_footer("No monster hunt actions to undo", success=False)
            else:
                set_footer(msg, success=True)
                render_calendar()

        render_calendar()
        return win

    def _open_monster_day_popup(self, parent_win, year, month, day, footer_setter, refresh_callback):
        monster_data = load_monster_csv()
        key = f"{year:04d}-{month:02d}"
        month_obj = monster_data.get(key, {})
        day_obj = month_obj.get(str(day), {"members": "", "time": "", "map": MAPS_7_12[0], "server": SERVERS[0], "done": False, "note": "", "proof": ""})

        win = ctk.CTkToplevel(parent_win)
        win.title(f"Monster Hunt — {year}-{month:02d}-{day:02d}")
        win.grab_set()
        self._register_popup(win)
        win.configure(fg_color="#050505")

        frm = ctk.CTkFrame(win, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(frm, text=f"Day {day} — {calendar.day_name[datetime.date(year, month, day).weekday()]}", text_color="#f1c40f", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(6,6))

        ctk.CTkLabel(frm, text="Number of players joined", text_color="#e5e7eb").pack(anchor="w", pady=(6,2))
        members_var = tk.StringVar(value=str(day_obj.get("members") or ""))
        members_entry = ctk.CTkEntry(frm, textvariable=members_var, width=260)
        members_entry.pack(anchor="w", pady=(0,6))

        ctk.CTkLabel(frm, text="Time (e.g., 20:30)", text_color="#e5e7eb").pack(anchor="w", pady=(6,2))
        time_var = tk.StringVar(value=day_obj.get("time") or "")
        time_entry = ctk.CTkEntry(frm, textvariable=time_var, width=260)
        time_entry.pack(anchor="w", pady=(0,6))

        ctk.CTkLabel(frm, text="Map (Map 7 - Map 12)", text_color="#e5e7eb").pack(anchor="w", pady=(6,2))
        map_var = tk.StringVar(value=day_obj.get("map") or MAPS_7_12[0])
        map_cb = ctk.CTkComboBox(frm, values=MAPS_7_12, variable=map_var, width=260)
        map_cb.pack(anchor="w", pady=(0,6))
        map_cb.set(map_var.get())

        ctk.CTkLabel(frm, text="Server", text_color="#e5e7eb").pack(anchor="w", pady=(6,2))
        server_var = tk.StringVar(value=day_obj.get("server") or SERVERS[0])
        server_cb = ctk.CTkComboBox(frm, values=SERVERS, variable=server_var, width=260)
        server_cb.pack(anchor="w", pady=(0,6))
        server_cb.set(server_var.get())

        ctk.CTkLabel(frm, text="Note (optional)", text_color="#e5e7eb").pack(anchor="w", pady=(6,2))
        note_var = tk.StringVar(value=day_obj.get("note") or "")
        note_entry = ctk.CTkEntry(frm, textvariable=note_var, width=420)
        note_entry.pack(anchor="w", pady=(0,6))

        ctk.CTkLabel(frm, text="Proof path (optional)", text_color="#e5e7eb").pack(anchor="w", pady=(6,2))
        proof_var = tk.StringVar(value=day_obj.get("proof") or "")
        proof_entry = ctk.CTkEntry(frm, textvariable=proof_var, width=420)
        proof_entry.pack(anchor="w", pady=(0,6))

        done_var = tk.BooleanVar(value=bool(day_obj.get("done")))
        ctk.CTkCheckBox(frm, text="Mark hunt as done (show ✖)", variable=done_var).pack(anchor="w", pady=(6,6))

        btn_frame = ctk.CTkFrame(frm, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(8,4))
        def on_save():
            try:
                members_val = members_var.get().strip()
                members_int = int(members_val) if members_val != "" else ""
            except Exception:
                footer_setter("Members must be a number", success=False)
                return
            monster_data_local = load_monster_csv()
            month_local = monster_data_local.get(key, {})
            before = month_local.get(str(day), {}).copy() if str(day) in month_local else {}
            month_local[str(day)] = {
                "members": members_int,
                "time": time_var.get().strip(),
                "map": map_var.get().strip(),
                "server": server_var.get().strip(),
                "done": bool(done_var.get()),
                "note": note_var.get().strip(),
                "proof": proof_var.get().strip()
            }
            monster_data_local[key] = month_local
            append_monster_log("save_day", year, month, day, before=before, after=month_local[str(day)])
            save_monster_csv(monster_data_local)
            footer_setter(f"Saved {year}-{month:02d}-{day:02d}: members={members_int}, map={map_var.get()}, server={server_var.get()}", success=True)
            refresh_callback()
            self._unregister_and_close(win)
        def on_clear():
            monster_data_local = load_monster_csv()
            month_local = monster_data_local.get(key, {})
            before = month_local.get(str(day), {}).copy() if str(day) in month_local else {}
            if str(day) in month_local:
                month_local.pop(str(day), None)
            monster_data_local[key] = month_local
            append_monster_log("clear_day", year, month, day, before=before, after={})
            save_monster_csv(monster_data_local)
            footer_setter(f"Cleared data for {year}-{month:02d}-{day:02d}", success=True)
            refresh_callback()
            self._unregister_and_close(win)
        ctk.CTkButton(btn_frame, text="Save", fg_color="#16a34a", command=on_save).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Clear", fg_color="#991b1b", command=on_clear).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#334155", command=lambda: self._unregister_and_close(win)).pack(side="left", padx=6)

        self._autosize_and_center(win, padding=(10,10), min_size=(420,360), center_on="screen")

    # ---------------- Global Search (app-only) ----------------
    def show_search(self, event=None):
        win = ctk.CTkToplevel(self)
        win.title("Global Search")
        win.grab_set()
        self._register_popup(win)
        win.configure(fg_color="#050505")

        frm = ctk.CTkFrame(win, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frm, text="Search Tag or Name (live)", text_color="#f1c40f").pack(anchor="w", pady=(6,4))
        qvar = tk.StringVar()
        entry = ctk.CTkEntry(frm, textvariable=qvar, width=520)
        entry.pack(pady=4)

        results_frame = tk.Frame(frm, bg="#0b0b0b")
        results_frame.pack(fill="both", expand=True, pady=(8,4))
        res_tree = ttk.Treeview(results_frame, columns=("table","tag","name","extra"), show="headings", height=12, style="Custom.Treeview")
        res_tree.heading("table", text="Table")
        res_tree.heading("tag", text="Tag")
        res_tree.heading("name", text="Name")
        res_tree.heading("extra", text="Extra")
        res_tree.column("table", width=100, anchor="w")
        res_tree.column("tag", width=140, anchor="w")
        res_tree.column("name", width=200, anchor="w")
        res_tree.column("extra", width=300, anchor="w")
        res_tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=res_tree.yview)
        res_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        details = tk.Text(frm, height=8, bg="#0b0b0b", fg="#e5e7eb", relief="flat", bd=0)
        details.pack(fill="both", expand=False, pady=(6,0))

        search_after_id = None
        def schedule_search(*_):
            nonlocal search_after_id
            if search_after_id:
                try:
                    win.after_cancel(search_after_id)
                except Exception:
                    pass
            search_after_id = win.after(180, do_search)

        def do_search():
            q = (qvar.get() or "").strip().lower()
            for it in res_tree.get_children():
                res_tree.delete(it)
            details.configure(state="normal")
            details.delete("1.0", "end")
            if not q:
                details.insert("1.0", "Type to search Tag or Name.")
                details.configure(state="disabled")
                return
            found = []
            for t in TABLES.keys():
                for r in self.load_table(t):
                    if q in (r.get("Tag","") or "").lower() or q in (r.get("Name","") or "").lower():
                        extra = []
                        for h in TABLES[t]["headers"]:
                            if h not in ("Tag","Name"):
                                v = r.get(h,"")
                                if v:
                                    extra.append(f"{h}:{v}")
                        found.append((t, r.get("Tag",""), r.get("Name",""), "; ".join(extra)))
            if not found:
                details.configure(state="normal")
                details.insert("1.0", "No table results.\n")
                details.configure(state="disabled")
            else:
                for t, tag, name, extra in found:
                    res_tree.insert("", "end", values=(t, tag, name, extra))

        def on_result_double_click(event):
            row_id = res_tree.identify_row(event.y)
            if not row_id:
                return
            vals = res_tree.item(row_id).get("values", [])
            if not vals or len(vals) < 2:
                return
            table = vals[0]
            tag = vals[1]
            self.open_record_in_view(table, tag)
            try:
                self._unregister_and_close(win)
            except Exception:
                pass

        def on_select(event):
            sel = res_tree.selection()
            if not sel:
                return
            vals = res_tree.item(sel[0])["values"]
            if not vals:
                return
            table, tag, name, extra = vals
            details.configure(state="normal")
            details.delete("1.0", "end")
            details.insert("1.0", f"Table: {table}\nTag: {tag}\nName: {name}\nExtra: {extra}\n")
            for r in self.load_table(table):
                if (r.get("Tag") or "") == tag:
                    details.insert("end", "\nFull record:\n")
                    for h in TABLES[table]["headers"]:
                        details.insert("end", f"{h}: {r.get(h,'')}\n")
                    break
            details.configure(state="disabled")

        res_tree.bind("<<TreeviewSelect>>", on_select)
        res_tree.bind("<Double-1>", on_result_double_click)
        qvar.trace_add("write", lambda *a: schedule_search())

        entry.focus_set()
        self._autosize_and_center(win, padding=(20,20), min_size=(640,360), center_on="screen")
        return win

    # ---------------- Settings / Close ----------------
    def show_settings(self):
        win = ctk.CTkToplevel(self)
        win.title("Settings")
        win.grab_set()
        self._register_popup(win)
        win.configure(fg_color="#050505")
        frm = ctk.CTkFrame(win, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frm, text="Settings", text_color="#f1c40f", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(6,4))

        # Clan name setting
        ctk.CTkLabel(frm, text="Clan name (used across the app)", text_color="#e5e7eb").pack(anchor="w", pady=(8,2))
        clan_name_var = tk.StringVar(value=self.clan_name)
        clan_entry = ctk.CTkEntry(frm, textvariable=clan_name_var, width=320)
        clan_entry.pack(anchor="w", pady=(0,6))

        def on_save_settings():
            new_name = (clan_name_var.get() or "").strip()
            if not new_name:
                messagebox.showerror("Settings", "Clan name cannot be empty.")
                return
            self.clan_name = new_name
            self.settings["clan_name"] = new_name
            save_settings(self.settings)
            # update UI texts that use clan name
            try:
                self.title(f"{self.clan_name} Clan — Actions")
                self.clan_label_var.set(f"{self.clan_name} Clan — Actions")
            except Exception:
                pass
            messagebox.showinfo("Settings", "Clan name updated.")
            self._unregister_and_close(win)

        ctk.CTkButton(frm, text="Save Settings", fg_color="#16a34a", command=on_save_settings).pack(pady=(12,6))
        ctk.CTkButton(frm, text="Close", fg_color="#334155", command=lambda: self._unregister_and_close(win)).pack()
        self._autosize_and_center(win, padding=(20,20), min_size=(360,220), center_on="screen")

    def on_close(self):
        try:
            for w in list(self._open_popups):
                try:
                    w.destroy()
                except Exception:
                    pass
            self.destroy()
        except Exception:
            try:
                self.quit()
            except Exception:
                pass

    # ---------------- Misc UI helpers ----------------
    def _register_popup(self, win: tk.Toplevel):
        try:
            self._open_popups.add(win)
            win.protocol("WM_DELETE_WINDOW", lambda w=win: self._unregister_and_close(w))
        except Exception:
            pass

    def _unregister_and_close(self, win: tk.Toplevel):
        try:
            if win in self._open_popups:
                self._open_popups.remove(win)
            try:
                win.grab_release()
            except Exception:
                pass
            try:
                win.destroy()
            except Exception:
                pass
        except Exception:
            pass

    def _autosize_and_center(self, win: tk.Toplevel, padding=(10,10), min_size=(300,200), center_on="parent"):
        try:
            win.update_idletasks()
            w = max(min_size[0], win.winfo_reqwidth() + padding[0])
            h = max(min_size[1], win.winfo_reqheight() + padding[1])
            if center_on == "screen":
                sw = win.winfo_screenwidth()
                sh = win.winfo_screenheight()
                x = (sw - w) // 2
                y = (sh - h) // 2
            else:
                px = self.winfo_rootx()
                py = self.winfo_rooty()
                pw = self.winfo_width()
                ph = self.winfo_height()
                x = px + (pw - w) // 2
                y = py + (ph - h) // 2
            win.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

# ---------------- Run ----------------
if __name__ == "__main__":
    app = DesiClanManager()
    app.mainloop()
