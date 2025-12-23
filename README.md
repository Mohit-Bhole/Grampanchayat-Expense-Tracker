# Grampanchayat Expense Tracker - Lakhalgaon

A simple, modern transparency portal for Lakhalgaon (Nashik) to publish grampanchayat expenses. Built with Python (Flask) and SQLite.

##Screenshots
[Link1](https://github.com/Mohit-Bhole/Grampanchayat-Expense-Tracker/blob/fe7ec9b5e64f4b73362a0d72d4b3367da2e9b84d/Screenshot%202025-12-23%20123939.png)
[Link2](https://github.com/Mohit-Bhole/Grampanchayat-Expense-Tracker/blob/fe7ec9b5e64f4b73362a0d72d4b3367da2e9b84d/Screenshot%202025-12-23%20125717.png)
[Link3](https://github.com/Mohit-Bhole/Grampanchayat-Expense-Tracker/blob/fe7ec9b5e64f4b73362a0d72d4b3367da2e9b84d/Screenshot%202025-12-23%20125746.png)
[Link4](https://github.com/Mohit-Bhole/Grampanchayat-Expense-Tracker/blob/fe7ec9b5e64f4b73362a0d72d4b3367da2e9b84d/Screenshot%202025-12-23%20125807.png)
[Link5](https://github.com/Mohit-Bhole/Grampanchayat-Expense-Tracker/blob/fe7ec9b5e64f4b73362a0d72d4b3367da2e9b84d/Screenshot%202025-12-23%20125842.png)
[Link6](https://github.com/Mohit-Bhole/Grampanchayat-Expense-Tracker/blob/fe7ec9b5e64f4b73362a0d72d4b3367da2e9b84d/Screenshot%202025-12-23%20125842.png)
[Link7](https://github.com/Mohit-Bhole/Grampanchayat-Expense-Tracker/blob/fe7ec9b5e64f4b73362a0d72d4b3367da2e9b84d/Screenshot%202025-12-23%20125900.png)

## Features
- Public portal to view latest expenses, filter by category and date
- Interactive monthly spending chart (Chart.js)
- CSV export for filtered expenses
- Admin login (default admin/admin123; change via env)
- Admin dashboard to add expenses, categories, and announcements

## Tech
- Backend: Flask + SQLAlchemy (SQLite)
- Frontend: Jinja templates, Chart.js, custom CSS

## Getting Started (Windows PowerShell)

1) Create & activate a virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies
```powershell
pip install -r requirements.txt
```

3) (Optional) Set environment variables
```powershell
$env:SECRET_KEY = "please-change-me"
$env:ADMIN_USER = "admin"
$env:ADMIN_PASS = "strong-password"
```

4) Run the server
```powershell
python app.py
```

Open `http://127.0.0.1:5000/` for the Public Portal.
Open `http://127.0.0.1:5000/admin/login` for Admin.

## Notes
- Database file: `grampanchayat_expense.db` (created on first run)
- Default categories are seeded on first run
- To reset, delete the `.db` file and restart

