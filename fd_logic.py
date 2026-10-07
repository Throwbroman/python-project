"""
fd_logic.py
-----------
Core business logic for the Fixed Deposit Maturity & Renewal Manager.

This module is deliberately kept independent of Flask/SQLite so it can be
tested (and reasoned about) in complete isolation, per the build guide's
advice to "test each piece before building anything on top of it."

Two bottlenecks called out in the guide are handled explicitly here:
  1. Leap-year-safe date math (calendar-aware month addition, not a flat
     365-day approximation).
  2. Premature closure using the penalty rate and the ACTUAL holding
     period, kept in its own function rather than patched onto the
     normal maturity formula.
"""

import calendar
from datetime import date, timedelta


# ---------------------------------------------------------------------
# Calendar-aware date math (fixes the "flat 365 days" bottleneck)
# ---------------------------------------------------------------------

def add_months(source_date: date, months: int) -> date:
    """
    Add a whole number of months to a date, correctly handling year
    rollovers, variable month lengths, and Feb 29 in leap years.

    Example: Jan 31, 2024 + 1 month -> Feb 29, 2024 (clamped to the
    actual last day of February in a leap year), not Mar 2.
    """
    month_index = source_date.month - 1 + months
    year = source_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def calculate_maturity_date(start_date: date, tenure_years: float) -> date:
    """
    Convert a tenure given in years (which may be fractional, e.g. 1.5
    years for 18 months) into an actual calendar date, using real month
    addition instead of `start_date + timedelta(days=tenure_years*365)`.

    This is the fix for the guide's Step 8 note: it correctly accounts
    for Feb 29 and variable month lengths instead of a flat day count.
    """
    total_months = round(tenure_years * 12)
    return add_months(start_date, total_months)


def days_between(start_date: date, end_date: date) -> int:
    """Actual calendar days between two dates (includes leap days)."""
    return (end_date - start_date).days


# ---------------------------------------------------------------------
# Step 5 — Quarterly compound interest (the core formula)
# ---------------------------------------------------------------------

def calculate_maturity_value(principal: float, annual_rate: float,
                              tenure_years: float, n: int = 4) -> float:
    """
    Maturity Value = P * (1 + r/n)^(n*t)

    principal      : amount deposited
    annual_rate    : annual interest rate as a percentage (e.g. 7.0 for 7%)
    tenure_years   : time in years (can be fractional)
    n              : compounding periods per year (4 = quarterly, fixed
                      default per this project)
    """
    r = annual_rate / 100
    maturity_value = principal * (1 + r / n) ** (n * tenure_years)
    return round(maturity_value, 2)


def calculate_maturity_value_by_date(principal: float, annual_rate: float,
                                      start_date: date, tenure_years: float,
                                      n: int = 4):
    """
    A more precise variant: computes the real maturity date first (calendar
    aware), then derives the elapsed time in years from the ACTUAL number
    of days (using 365.25 to average in leap years) rather than the raw
    tenure_years input. Returns (maturity_value, maturity_date).

    This is the version the app actually uses for display, since it
    folds in the leap-year fix from Step 8 automatically.
    """
    maturity_date = calculate_maturity_date(start_date, tenure_years)
    actual_days = days_between(start_date, maturity_date)
    t = actual_days / 365.25
    value = calculate_maturity_value(principal, annual_rate, t, n)
    return value, maturity_date


# ---------------------------------------------------------------------
# Step 6 — Premature closure (kept as its own explicit code path)
# ---------------------------------------------------------------------

def calculate_premature_closure_value(principal: float, annual_rate: float,
                                       penalty_rate: float,
                                       start_date: date, closure_date: date,
                                       n: int = 4) -> float:
    """
    Applies the penalty rate instead of the originally agreed rate, and
    recalculates interest only for the ACTUAL time the money was held
    (start_date -> closure_date), using real calendar days.
    """
    effective_rate = annual_rate - penalty_rate
    actual_days = days_between(start_date, closure_date)
    actual_years = actual_days / 365.25
    r = effective_rate / 100
    value = principal * (1 + r / n) ** (n * actual_years)
    return round(value, 2)


# ---------------------------------------------------------------------
# Step 8 — "Maturing in the next N days" list
# ---------------------------------------------------------------------

def get_days_left(maturity_date: date, today: date = None) -> int:
    today = today or date.today()
    return (maturity_date - today).days


def is_maturing_soon(maturity_date: date, days_window: int = 30,
                      today: date = None) -> bool:
    days_left = get_days_left(maturity_date, today)
    return 0 <= days_left <= days_window
