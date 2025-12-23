import os
import csv
from datetime import datetime, date
from functools import wraps
from typing import Optional

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, scoped_session
from werkzeug.security import generate_password_hash, check_password_hash

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///grampanchayat_expense.db")
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")
DEFAULT_ADMIN_USER = os.getenv("ADMIN_USER", "admin")
DEFAULT_ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")
VILLAGE_NAME = "Lakhalgaon"
APP_NAME = "Grampanchayat Expense Tracker"

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

@app.context_processor
def inject_globals():
	return {"datetime": datetime}

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
Base = declarative_base()
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))


class AdminUser(Base):
	__tablename__ = "admin_users"
	id = Column(Integer, primary_key=True)
	username = Column(String(50), unique=True, nullable=False)
	password_hash = Column(String(255), nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow)


class Category(Base):
	__tablename__ = "categories"
	id = Column(Integer, primary_key=True)
	name = Column(String(100), unique=True, nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow)
	expenses = relationship("Expense", back_populates="category", cascade="all, delete-orphan")


class Expense(Base):
	__tablename__ = "expenses"
	id = Column(Integer, primary_key=True)
	title = Column(String(200), nullable=False)
	amount = Column(Float, nullable=False)
	date_spent = Column(Date, nullable=False)
	description = Column(String(1000), nullable=True)
	receipt_url = Column(String(500), nullable=True)
	category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow)

	category = relationship("Category", back_populates="expenses")


class Announcement(Base):
	__tablename__ = "announcements"
	id = Column(Integer, primary_key=True)
	title = Column(String(200), nullable=False)
	body = Column(String(2000), nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
	Base.metadata.create_all(bind=engine)
	db = SessionLocal()
	try:
		# Seed admin user
		if db.query(AdminUser).count() == 0:
			admin = AdminUser(username=DEFAULT_ADMIN_USER, password_hash=generate_password_hash(DEFAULT_ADMIN_PASS))
			db.add(admin)
			db.commit()
		# Seed default category
		if db.query(Category).count() == 0:
			for name in ["Roads", "Water", "Electricity", "Sanitation", "Education", "Health", "Public Works", "Other"]:
				db.add(Category(name=name))
			db.commit()
		# Seed welcome announcement
		if db.query(Announcement).count() == 0:
			db.add(Announcement(title=f"Welcome to {APP_NAME}", body=f"This portal shows where {VILLAGE_NAME} Grampanchayat spends public funds."))
			db.commit()
	finally:
		db.close()


init_db()


# Auth utilities

def login_required(view_func):
	@wraps(view_func)
	def wrapped(*args, **kwargs):
		if not session.get("admin_logged_in"):
			return redirect(url_for("admin_login", next=request.path))
		return view_func(*args, **kwargs)
	return wrapped


# Routes - Public/User
@app.route("/")
def user_home():
	db = SessionLocal()
	try:
		categories = db.query(Category).order_by(Category.name.asc()).all()
		announcements = db.query(Announcement).order_by(Announcement.created_at.desc()).limit(5).all()

		# Filters
		category_id = request.args.get("category_id")
		start_date_str = request.args.get("start_date")
		end_date_str = request.args.get("end_date")

		q = db.query(Expense).order_by(Expense.date_spent.desc())
		if category_id:
			q = q.filter(Expense.category_id == int(category_id))
		if start_date_str:
			try:
				start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
				q = q.filter(Expense.date_spent >= start_date)
			except ValueError:
				pass
		if end_date_str:
			try:
				end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
				q = q.filter(Expense.date_spent <= end_date)
			except ValueError:
				pass
		expenses = q.limit(200).all()

		total_spent = sum(e.amount for e in expenses)

		return render_template(
			"user_home.html",
			app_name=APP_NAME,
			village_name=VILLAGE_NAME,
			categories=categories,
			announcements=announcements,
			expenses=expenses,
			total_spent=total_spent,
			selected_category_id=int(category_id) if category_id else None,
			start_date=start_date_str or "",
			end_date=end_date_str or "",
		)
	finally:
		db.close()


@app.route("/api/expenses_summary")
def api_expenses_summary():
	db = SessionLocal()
	try:
		# Optional filters
		category_id = request.args.get("category_id")
		start_date_str = request.args.get("start_date")
		end_date_str = request.args.get("end_date")

		q = db.query(
			func.strftime("%Y-%m", Expense.date_spent).label("month"),
			func.sum(Expense.amount).label("total")
		)
		if category_id:
			q = q.filter(Expense.category_id == int(category_id))
		if start_date_str:
			try:
				start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
				q = q.filter(Expense.date_spent >= start_date)
			except ValueError:
				pass
		if end_date_str:
			try:
				end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
				q = q.filter(Expense.date_spent <= end_date)
			except ValueError:
				pass

		q = q.group_by("month").order_by("month")
		data = q.all()
		labels = [row.month for row in data]
		totals = [float(row.total or 0) for row in data]
		return jsonify({"labels": labels, "totals": totals})
	finally:
		db.close()


@app.route("/api/export.csv")
def api_export_csv():
	db = SessionLocal()
	try:
		category_id = request.args.get("category_id")
		start_date_str = request.args.get("start_date")
		end_date_str = request.args.get("end_date")

		q = db.query(Expense).order_by(Expense.date_spent.desc())
		if category_id:
			q = q.filter(Expense.category_id == int(category_id))
		if start_date_str:
			try:
				start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
				q = q.filter(Expense.date_spent >= start_date)
			except ValueError:
				pass
		if end_date_str:
			try:
				end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
				q = q.filter(Expense.date_spent <= end_date)
			except ValueError:
				pass
		expenses = q.all()

		filename = "expenses_export.csv"
		header = ["ID", "Title", "Amount", "Date", "Category", "Description", "Receipt URL"]
		with open(filename, "w", newline="", encoding="utf-8") as f:
			writer = csv.writer(f)
			writer.writerow(header)
			for e in expenses:
				writer.writerow([
					e.id,
					e.title,
					f"{e.amount:.2f}",
					e.date_spent.isoformat(),
					e.category.name if e.category else "",
					e.description or "",
					e.receipt_url or "",
				])
		return send_file(filename, as_attachment=True)
	finally:
		db.close()


# Routes - Admin
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
	if request.method == "POST":
		username = request.form.get("username", "").strip()
		password = request.form.get("password", "").strip()
		db = SessionLocal()
		try:
			user = db.query(AdminUser).filter(AdminUser.username == username).first()
			if user and check_password_hash(user.password_hash, password):
				session["admin_logged_in"] = True
				session["admin_username"] = user.username
				return redirect(url_for("admin_dashboard"))
			flash("Invalid credentials", "error")
		finally:
			db.close()
	return render_template("admin_login.html", app_name=APP_NAME, village_name=VILLAGE_NAME)


@app.route("/admin/logout")
@login_required
def admin_logout():
	session.clear()
	return redirect(url_for("admin_login"))


@app.route("/admin")
@login_required
def admin_dashboard():
	db = SessionLocal()
	try:
		categories = db.query(Category).order_by(Category.name.asc()).all()
		recent_expenses = db.query(Expense).order_by(Expense.created_at.desc()).limit(10).all()
		announcements = db.query(Announcement).order_by(Announcement.created_at.desc()).limit(5).all()
		return render_template(
			"admin_dashboard.html",
			app_name=APP_NAME,
			village_name=VILLAGE_NAME,
			categories=categories,
			expenses=recent_expenses,
			announcements=announcements,
		)
	finally:
		db.close()


@app.route("/admin/expense/new", methods=["POST"])
@login_required
def admin_create_expense():
	title = request.form.get("title", "").strip()
	amount = request.form.get("amount")
	date_spent = request.form.get("date_spent")
	description = request.form.get("description")
	receipt_url = request.form.get("receipt_url")
	category_id = request.form.get("category_id")

	if not title or not amount or not date_spent or not category_id:
		flash("Please fill all required fields.", "error")
		return redirect(url_for("admin_dashboard"))

	try:
		amount_val = float(amount)
		date_val = datetime.strptime(date_spent, "%Y-%m-%d").date()
		category_val = int(category_id)
	except Exception:
		flash("Invalid form values.", "error")
		return redirect(url_for("admin_dashboard"))

	db = SessionLocal()
	try:
		exp = Expense(
			title=title,
			amount=amount_val,
			date_spent=date_val,
			description=description,
			receipt_url=receipt_url,
			category_id=category_val,
		)
		db.add(exp)
		db.commit()
		flash("Expense added successfully.", "success")
	finally:
		db.close()

	return redirect(url_for("admin_dashboard"))


@app.route("/admin/category/new", methods=["POST"])
@login_required
def admin_create_category():
	name = request.form.get("name", "").strip()
	if not name:
		flash("Category name is required.", "error")
		return redirect(url_for("admin_dashboard"))

	db = SessionLocal()
	try:
		exists = db.query(Category).filter(func.lower(Category.name) == name.lower()).first()
		if exists:
			flash("Category already exists.", "error")
		else:
			db.add(Category(name=name))
			db.commit()
			flash("Category created.", "success")
	finally:
		db.close()

	return redirect(url_for("admin_dashboard"))


@app.route("/admin/announcement/new", methods=["POST"])
@login_required
def admin_create_announcement():
	title = request.form.get("title", "").strip()
	body = request.form.get("body", "").strip()
	if not title or not body:
		flash("Title and body are required.", "error")
		return redirect(url_for("admin_dashboard"))

	db = SessionLocal()
	try:
		db.add(Announcement(title=title, body=body))
		db.commit()
		flash("Announcement published.", "success")
	finally:
		db.close()

	return redirect(url_for("admin_dashboard"))


# Error handlers
@app.errorhandler(404)
def not_found(_):
	return render_template("404.html", app_name=APP_NAME, village_name=VILLAGE_NAME), 404


@app.errorhandler(500)
def server_error(_):
	return render_template("500.html", app_name=APP_NAME, village_name=VILLAGE_NAME), 500


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
