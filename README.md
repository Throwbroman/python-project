# FD Manager (my Fixed Deposit app)

Hey! So this is a little app I made to keep track of Fixed Deposits (FDs) for a bank kind of thing. Basically it stores FD info, tells you how much money you'll get when it matures, and warns you if one is about to mature soon so you can call the customer.

I'm still learning Python so go easy on me lol. This is my first "real" project with a database and a website part.

## What it actually does

- You add an FD (customer name, how much money, interest rate, when it started, how long it runs for)
- It does the math for you (quarterly compounding, whatever that means lol, basically your money grows every 3 months)
- It shows you a list of ALL your FDs
- It shows you which ones are gonna mature in the next 30 days (so you dont forget to call the customer)
- You can also close an FD early if someone needs their money before it matures (there's a penalty for that, banks do that in real life apparently)

## Files (what's what)

- `app.py` - this is the main file, it's the website basically. run this one
- `fd_logic.py` - all the math stuff is here (interest calculations etc)
- `database.py` - this talks to the database (saves your FDs so they dont disappear when you close the app)
- `templates/` folder - the actual web pages (html files)
- `requirements.txt` - just says "hey you need Flask installed"
- `BUILD_EXE.md` - if you want to turn this into an actual .exe file you can double click, read this one

## How to run it (do this first)

1. make sure you have python installed (get it from python.org, and when installing CHECK THE BOX that says "add to PATH" or nothing will work)
2. open a terminal in this folder
3. type this and hit enter:
   ```
   pip install -r requirements.txt
   ```
4. then type:
   ```
   python app.py
   ```
5. open your browser and go to `http://127.0.0.1:5000`
6. thats it, ur in

If you're using PyCharm just open the folder as a project, set up the interpreter thing (it usually asks you), then right click app.py and hit Run. Same result.

## How the math works (in case you're curious)

The formula for figuring out how much your FD is worth at the end is:

```
Maturity Value = P x (1 + r/n)^(n x t)
```

- P = how much money you put in
- r = interest rate (like 7% but as 0.07)
- n = how many times a year it compounds (I hardcoded this to 4 = quarterly, banks usually do this every 3 months)
- t = how many years

I didn't come up with this, it's just the normal compound interest formula, I just wrote it in python:

```python
def calculate_maturity_value(principal, annual_rate, tenure_years, n=4):
    r = annual_rate / 100
    maturity_value = principal * (1 + r / n) ** (n * tenure_years)
    return round(maturity_value, 2)
```

### the leap year thing (this took me a while to figure out)

At first I was just doing `start_date + 365 days` to figure out when something matures but that's WRONG because some years have 366 days (leap years, February has 29 days instead of 28). So if I just multiply years x 365 the maturity date ends up being off by a day sometimes. Fixed it by actually adding real calendar months instead of just adding a flat number of days. Python has good date stuff built in for this (the `datetime` module).

### the early closure thing

If someone takes their money out early, the bank doesn't give them the full interest rate, they knock some percentage off (the "penalty rate"). I made this its own separate function instead of trying to shove it into the normal maturity function because I kept confusing myself when I tried to combine them lol.

## Stuff I tested

I made myself test 3 things before calling this "done" (some guide I was following told me to do this and it actually helped catch bugs):

1. an FD that spans Feb 29 in a leap year - to make sure the date math doesn't break
2. closing an FD early - making sure it uses the penalty rate and not the full rate
3. the "maturing soon" list - made fake FDs that mature in exactly 0 days, 30 days, and 31 days, and checked that the 31 day one does NOT show up (it should only show stuff maturing within 30 days)

## Known issues / stuff I'd fix if I had more time

- there's no login/password thing, anyone who opens the app can see/edit/delete everything. probably fine for just messing around on my own laptop but definitely not "production ready"
- no way to edit an FD once you added it, you can only delete it and re-add it. kinda annoying, i know
- no search bar, if you have like 500 FDs you'd just have to scroll and look
- the interest rate math assumes quarterly compounding always, some real banks let you pick monthly/yearly too, I just hardcoded quarterly since that's what I needed
- error messages are pretty basic, it just kind of tells you "something went wrong" sometimes instead of exactly what

## Turning it into a real .exe (optional)

If you want people to be able to just double click a file and run this without installing python, check `BUILD_EXE.md`. Basically you run one command (`pyinstaller ...`) and it spits out a single file you can send to anyone.

---

made this while learning python + flask + sqlite, still figuring stuff out but it works!
