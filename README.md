# Student Course Management — Browser Version

This version opens in a web browser and uses Flask (Python) with SQLite for persistent local storage.

## Requirements
- Python 3.10 or newer
- VS Code (recommended)
- Internet is only needed to install Flask and to load the optional Google Fonts in the design; the app itself runs locally.

## Run on Windows
1. Extract the ZIP file.
2. Open the extracted `Student_Course_Management_Web` folder in VS Code.
3. Select **Terminal → New Terminal**.
4. (Recommended) Create a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, you can skip activation and continue with the next commands.
5. Install the dependency:
   ```powershell
   python -m pip install -r requirements.txt
   ```
6. Start the website:
   ```powershell
   python app.py
   ```
7. Open Chrome and visit **http://127.0.0.1:5000**.
8. Keep the terminal open while using the website. Press `Ctrl+C` in the terminal to stop it.

## Included features
- Browser-based dashboard with course and unit totals
- Eight requested courses preloaded on first launch
- Add, edit, delete, and search courses
- Automatic saving to `courses.db` (SQLite) and `courses.json`
- Explicit **Save to file** and **Load from file** controls for `courses.json`
- **Download JSON** link to download a copy of the course list
- Duplicate course-code validation and unit validation
- Responsive layout for mobile and desktop

## Saving and sharing
Course changes are saved automatically on the laptop in `courses.db` (the main SQLite database) and copied to `courses.json` in this same project folder. The app refreshes the JSON copy at startup and after every successful add, edit, or delete. You do not need to open either file manually. The **Save to file** button writes the current list to `courses.json`. The **Load from file** button reads `courses.json` and replaces the current database list with the file contents. The **Download JSON** link downloads a copy. Closing the browser or stopping and restarting the app does not delete saved records, as long as you keep the project folder and do not delete `courses.db`. To share the latest data, stop the app and share the project folder including `courses.db` and `courses.json`.

This is a **local web application**, not a public website. By default, it is only available on the computer running it at `127.0.0.1`. To let classmates access it from anywhere, it would need to be deployed to a web hosting service and configured with a suitable production database and security settings.

## Important security note
This is a coursework/demo app. Before public deployment, replace the development secret key, disable debug mode, add authentication/authorization as needed, and use production hosting/database settings.


## Upload and save buttons
- The app automatically stores the main database at `Documents/Student Course Management/courses.db`.
- **Save file** refreshes `courses.csv` in that same Documents folder.
- **Upload file** imports a `.csv` or `.json` course list from your laptop and updates the local database and CSV copy. Uploading replaces the current course list, so only upload a file you intend to use as the new list.
- **Download CSV** downloads a readable copy to your browser's download location.

For CSV uploads, include the columns `code`, `title`, and `units`. JSON uploads should contain a list of objects with those same fields.
