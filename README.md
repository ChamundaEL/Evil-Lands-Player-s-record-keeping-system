Hi everyone 👋  
I built a **Player Record Management system** for my clan, and I thought—why not share it with all of you? Maybe you’ll find the idea interesting, or even find the `.exe` file useful for managing your own clan records.

---

## 📦 Installation & Setup

1. **Download** the release package from the link below.
2. **Create a dedicated folder** (for example: `EvilRecords/`).
3. Place the downloaded `.exe` file inside this folder.  
   - The program will automatically create the required `.csv` files (`clan_table.csv`, `blacklisted_table.csv`, `removed_table.csv`, plus `monster_hunt.csv` and `monster_hunt_log.csv`) if they don’t already exist.
4. **Important**: Always keep the `.exe` file and the `.csv` files together in the same folder.  

To run the app, simply double‑click the `.exe` file.

---

## 🗂 Data Storage

The app uses CSV files for persistence:
- `clan_table.csv` — stores clan members
- `blacklisted_table.csv` — stores blacklisted players
- `removed_table.csv` — stores removed players
- `monster_hunt.csv` — stores Monster Hunt participation data (auto‑created)
- `monster_hunt_log.csv` — audit log of Monster Hunt actions (auto‑created)
- `settings.json` — stores app settings (like clan name)

All records you add, delete, or edit are automatically saved to these files.

---

## ✨ Features

1. **Search across three tables**: *Clan*, *Blacklisted*, and *Removed*.
2. **Global Search**: Live search across all tables with instant results.
3. **Move records**: Easily transfer player records between tables.
4. **Undo actions**: Undo moves or deletions to restore data.
5. **Quick Add**: Add new records quickly with clipboard paste support.
6. **View & Manage**: Paginated table view with edit, delete, move, and refresh options.
7. **Monster Hunt Module**:
   - Calendar view for current and previous month
   - Heatmap coloring by participation
   - Mark days as done/undone
   - Per‑day popup for editing details (members, time, map, server, notes, proof)
   - Analysis tools (participation per day, completed days, average members, detailed list)
   - Export analysis to CSV
   - Audit log with undo support
8. **Clan Settings**: Change the clan’s name (saved in `settings.json`).
9. **Keyboard Shortcuts**:
   - `F8` → Quick Add
   - `Ctrl+F` → Global Search
10. **Compact UI**: Dark theme, modern look, optimized for in‑game overlay use.

---

## 📥 Download

👉 [Direct Download EvilLandsPlayerRecords.exe](https://github.com/ChamundaEL/Evil-Lands-Player-s-record-keeping-system/raw/main/EvilLandsPlayerRecords.exe)

---

## 📝 Notes

- Always run the `.exe` from its dedicated folder with the CSV files present.
- If CSV files are missing, the program will auto‑create them.
- Data is portable — you can back up or share the CSV files directly.
- Future updates will keep the same folder structure, so upgrading is easy.
