from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.hash import bcrypt
import math
import os

# Config
SECRET_KEY = "0TMN0vfgRobMve_TQl7GRspHSCyDltQDaLnE7MlZuZw"
DATABASE_URL = "sqlite:///./db.sqlite3"

# App Init
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# DB Setup
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(254), unique=True, nullable=True)
    hashed_password = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        
# Helper fns
def get_current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if user_id:
        return db.query(User).filter(User.id == user_id).first()
    return None

def gcd(a, b):
    if (a == 0):
        return b
    return gcd(b % a, a)
    
def lcm(arr, idx):
    if (idx == len(arr)-1):
        return arr[idx]
    a = arr[idx]
    b = lcm(arr, idx+1)
    return int(a*b/gcd(a,b))

# Auth
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("calc/index.html", {"request": request, "user": get_current_user(request, db)})

@app.get("/login", response_class=HTMLResponse)
async def loginv(request: Request):
    return templates.TemplateResponse("calc/login.html", {"request": request})

@app.post("/login")
async def loginp(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if user and bcrypt.verify(password, user.hashed_password):
        request.session["user_id"] = user.id
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("calc/login.html", {"request": request, "message": "Invalid username and/or password."})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)

@app.get("/register", response_class=HTMLResponse)
async def registerv(request: Request):
    return templates.TemplateResponse("calc/register.html", {"request": request})

@app.post("/register")
async def registerp(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), confirmation: str = Form(...), db: Session = Depends(get_db)):
    if password != confirmation:
        return templates.TemplateResponse("calc/register.html", {"request": request, "message": "Passwords must match."})
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("calc/register.html", {"request": request, "message": "Username already taken."})
    user = User(username=username, email=email, hashed_password=bcrypt.hash(password))
    db.add(user)
    db.commit()
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=302)
    
    
# Calc
@app.get("/trigo", response_class=HTMLResponse)
async def trigov(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("calc/trigo.html", {"request": request, "user": get_current_user(request, db)})
    
@app.get("/logln", response_class=HTMLResponse)
async def loglnv(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("calc/logln.html", {"request": request, "user": get_current_user(request, db)})

@app.post("/trigo", response_class=HTMLResponse)
async def trigop(request: Request, fn: str = Form(...), x: str = Form(...), unit: str = Form(...), db: Session = Depends(get_db)):
    x = int(x)
    if unit != "radian":
        x = x * math.pi/180
    res = 0
    if fn == "sin":
        res = math.sin(x)
    elif fn == "cos":
        res = math.cos(x)
    elif fn == "tan":
        res = math.tan(x)
    elif fn == "cosec":
        try:
            res = 1/math.sin(x)
        except:
            res = float('inf')
    elif fn == "sec":
        try:
            res = 1/math.cos(x)
        except:
            res = float('inf')
    elif fn == "cot":
        try:
            res = 1/math.tan(x)
        except:
            res = float('inf')
            
    if res >= 100000000000:
        res = float('inf')
    elif res <= -1000000000:
        res = float('inf')
        
    return templates.TemplateResponse("calc/trigo.html", {"request": request, "res": round(res, 2), "user": get_current_user(request, db)})
    
@app.post("/logln", response_class=HTMLResponse)
async def loglnp(request: Request, fn: str = Form(...), x: str = Form(...), base: str = Form(...), db: Session = Depends(get_db)):
    error = ""
    x = float(x)
    base = float(base)
    res = 0
    eorn = False
    if x <= 0:
        error = "Value must be +ve"
        eorn = True
        return templates.TemplateResponse("calc/logln.html", {"request": request, "error": error, "eorn": eorn, "user": get_current_user(request, db)})
    if fn == "log":
        if (base <= 0 or base == 1):
            error = "Base must be +ve or not 1"
            eorn = True
            return templates.TemplateResponse("calc/logln.html", {"request": request, "error": error, "eorn": eorn, "user": get_current_user(request, db)})
        res = math.log(x, base)
    else:
        res = math.log(x)
        
    return templates.TemplateResponse("calc/logln.html", {"request": request, "res": res, "eorn": eorn, "user": get_current_user(request, db)})

@app.get("/hcflcm", response_class=HTMLResponse)
async def hcflcmv(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("calc/hcflcm.html", {"request": request, "user": get_current_user(request, db)})

@app.post("/hcflcm", response_class=HTMLResponse)
async def hcflcmp(request: Request, fn: str = Form(...), x: str = Form(...), db: Session = Depends(get_db)):
    res = 0
    eorn = False
    error = ""
    y = (x.split(","))
    for z in y:
        if z == "0":
            error = "All numbers must be positive"
            eorn = True
            return templates.TemplateResponse("calc/hcflcm.html", {"request": request, "error": error, "eorn": eorn, "user": get_current_user(request, db)})
    if fn == "lcm":
        nl = []
        for i in range(len(y)):
            n = int(y[i])
            nl.append(n)
        res = lcm(nl,0)
    else:
        n1= int(y[0])
        n2= int(y[1])
        hcf=gcd(n1,n2)
        for i in range(2,len(y)):
            hcf=gcd(hcf,int(y[i]))
        res = hcf
    return templates.TemplateResponse("calc/hcflcm.html", {"request": request, "res": res, "eorn": eorn, "user": get_current_user(request, db)})

@app.get("/qe", response_class=HTMLResponse)
async def qev(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("calc/qe.html", {"request": request, "user": get_current_user(request, db)})

@app.post("/qe", response_class=HTMLResponse)
async def qep(request: Request, a: str = Form(...), b: str = Form(...), c: str = Form(...),db: Session = Depends(get_db)):
    error = ""
    eorn = False
    a = int(a)
    b = int(b)
    c = int(c)
    x1 = 0
    x2 = 0
    e1 = False
    e2 = False
    eb = False
    
    if (a <= 0):
        error = "a cannot be 0"
        eorn = True
        return templates.TemplateResponse("calc/qe.html", {"request": request, "eorn": eorn, "error": error, "user": get_current_user(request, db)})
        
    try:
        x1 = (-b+math.sqrt(b**2-4*a*c))/2*a
    except:
        e1 = True

    try:
        x2 = (-b-math.sqrt(b**2-4*a*c))/2*a
    except:
        e2 = True
        
    if (e1 and e2):
        eb = True
        e1 = False
        e2 = False
    
    return templates.TemplateResponse("calc/qe.html", {"request": request, "x1": round(x1,3), "x2": round(x2,3), "e1": e1, "e2": e2, "eb": eb, "eorn": eorn, "user": get_current_user(request, db)})
        
@app.get("/stats", response_class=HTMLResponse)
async def statsv(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("calc/stats.html", {"request": request, "user": get_current_user(request, db)})
    
@app.post("/stats", response_class=HTMLResponse)
async def statsp(request: Request, x: str = Form(...), db: Session = Depends(get_db)):
    y = (int(x).split(","))
    nl = []
    for i in range(len(y)):
        n = int(y[i])
        nl.append(n)
    nl.sort()
    m = 0
    for n in nl:
        m = m + n/len(nl)
    M = 0
    l = int(len(nl)/2)
    if len(nl)%2 == 0:
        M = (nl[l-1]+ nl[l])/2
    else:
        M = (nl[l])/2
    md = 0
    Md = 0
    vari = 0
    sd = 0
    for n in nl:
        md = md + abs(n-m)/len(nl)
        Md = Md + abs(n-M)/len(nl)
        vari = vari + (n-m)**2/len(nl)
    sd = math.sqrt(vari)
    r = max(nl) - min(nl)
    cv = m/sd*100

    return templates.TemplateResponse("calc/stats.html", {"request": request, "mean": m, "M": M, "meand": md, "Md": Md, "var": vari, "sd": round(sd, 3), "range": r, "cv": round(cv,3), "user": get_current_user(request, db)})
