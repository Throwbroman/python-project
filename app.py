"""
app.py
------
Flask web front-end (Step 12 of the build guide) wired directly on top of
the Step 5-9 logic. No calculation logic lives in this file — it only
collects input, calls the functions in fd_logic.py / database.py, and
renders results.

Run with:  python app.py
Then open: http://127.0.0.1:5000 in your browser.
"""

import os
import sys
import threading
import webbrowser
from datetime import date, datetime

from flask import Flask, render_template, request, redirect, url_for, flash

import database
import fd_logic


def _resource_dir():
    """
    Locate templates/static correctly whether running as a normal script
    or as a PyInstaller-frozen executable (which unpacks bundled files
    into a temp folder referenced by sys._MEIPASS).
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


_base = _resource_dir()
app = Flask(
    __name__,
    template_folder=os.path.join(_base, "templates"),
    static_folder=os.path.join(_base, "static"),
)
app.secret_key = "fd-manager-dev-key"  # fine for local/dev use


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def build_view_model(fd: dict) -> dict:
    """Attach computed fields (maturity value, maturity date, days left,
    status) to a raw database row for display in templates."""
    start_date = parse_date(fd["start_date"])
    maturity_value, maturity_date = fd_logic.calculate_maturity_value_by_date(
        fd["principal"], fd["rate"], start_date, fd["tenure_years"]
    )

    view = dict(fd)
    view["maturity_value"] = maturity_value
    view["maturity_date"] = maturity_date

    if fd["premature_closed"]:
        closure_date = parse_date(fd["closure_date"])
        view["closure_value"] = fd_logic.calculate_premature_closure_value(
            fd["principal"], fd["rate"], fd["penalty_rate"],
            start_date, closure_date
        )
        view["status"] = "Closed early"
        view["days_left"] = None
        view["maturing_soon"] = False
    else:
        days_left = fd_logic.get_days_left(maturity_date)
        view["days_left"] = days_left
        view["maturing_soon"] = fd_logic.is_maturing_soon(maturity_date)
        view["status"] = "Matured" if days_left < 0 else "Active"

    return view


@app.route("/")
def home():
    fds = [build_view_model(fd) for fd in database.get_all_fds()]
    return render_template("index.html", fds=fds, only_maturing=False)


@app.route("/maturing-soon")
def maturing_soon():
    fds = [build_view_model(fd) for fd in database.get_all_fds()]
    fds = [fd for fd in fds if fd["maturing_soon"]]
    return render_template("index.html", fds=fds, only_maturing=True)


@app.route("/add", methods=["GET", "POST"])
def add_fd():
    if request.method == "POST":
        try:
            customer = request.form["customer"].strip()
            account_no = request.form["account_no"].strip()
            principal = float(request.form["principal"])
            rate = float(request.form["rate"])
            start_date = parse_date(request.form["start_date"])
            tenure_years = float(request.form["tenure_years"])
            penalty_rate = float(request.form.get("penalty_rate") or 0)

            if not customer or not account_no:
                raise ValueError("Customer name and account number are required.")
            if principal <= 0 or rate < 0 or tenure_years <= 0:
                raise ValueError("Principal, rate and tenure must be positive numbers.")

            database.insert_fd(customer, account_no, principal, rate,
                                start_date, tenure_years, penalty_rate)
            flash(f"FD {account_no} added successfully.", "success")
            return redirect(url_for("home"))
        except ValueError as e:
            flash(str(e), "error")
        except Exception:
            flash("Could not add FD — check that account number is unique and all fields are valid.", "error")

    return render_template("add.html", today=date.today().isoformat())


@app.route("/close/<int:fd_id>", methods=["GET", "POST"])
def close_fd(fd_id):
    fd = database.get_fd(fd_id)
    if fd is None:
        flash("FD not found.", "error")
        return redirect(url_for("home"))

    if fd["premature_closed"]:
        flash("This FD is already marked as closed.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        try:
            closure_date = parse_date(request.form["closure_date"])
            start_date = parse_date(fd["start_date"])
            if closure_date <= start_date:
                raise ValueError("Closure date must be after the start date.")
            database.mark_premature_closed(fd_id, closure_date)
            flash(f"FD {fd['account_no']} marked as prematurely closed.", "success")
            return redirect(url_for("home"))
        except ValueError as e:
            flash(str(e), "error")

    return render_template("close.html", fd=fd, today=date.today().isoformat())


@app.route("/delete/<int:fd_id>", methods=["POST"])
def delete_fd(fd_id):
    database.delete_fd(fd_id)
    flash("FD deleted.", "success")
    return redirect(url_for("home"))


def _wait_for_server_then_open_browser(host="127.0.0.1", port=5000, timeout=15):
    """
    Poll the port until Flask is actually accepting connections, then open
    the browser. More reliable than a fixed delay, since a PyInstaller
    onefile build can take a variable amount of time to unpack itself
    and start listening.
    """
    import socket
    import time

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                break
        except OSError:
            time.sleep(0.25)
    try:
        webbrowser.open(f"http://{host}:{port}")
    except Exception:
        pass  # worst case, the person clicks the link in the console themselves


if __name__ == "__main__":
    database.setup_database()
    frozen = getattr(sys, "frozen", False)

    if frozen:
        # Packaged executable: wait for the server to actually be ready,
        # then open the browser automatically. Run without the debug
        # reloader (which doesn't work inside a PyInstaller onefile bundle)
        # and without debug mode.
        threading.Thread(target=_wait_for_server_then_open_browser, daemon=True).start()
        app.run(debug=False, use_reloader=False)
    else:
        # Normal development: keep debug mode for auto-reload on code changes.
        app.run(debug=True)