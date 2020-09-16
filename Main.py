from flask import Flask, request, render_template, session, redirect, url_for
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from tinydb import TinyDB, Query
import requests, bs4, os

from config import *

db = TinyDB("db.tinydb")
query = Query()

Codes = {
    "B01":"綜合大樓",
    "C01":"工學院",
    "C02":"理學院",
    "K01":"體育休閒大樓",
    "L01":"圖資大樓",
    "L02":"法學院",
    "M01":"管學院",
    "H1-":"人社科學院",
    "H2-":"人社科學院"
    }

Log = str(datetime.now())[:-7].replace(" ", "_").replace(":","_") + ".log"
# ----- Functions -----
def logger(msg, code = 0):
    #0 to 4 are available
    FolderInit(LoggerPath)
    with open(LoggerPath + Log, "a+", encoding='UTF-8') as file:
        buffer = "{0} | {1} : {2}".format(types[code], datetime.now(), msg)
        print(buffer)
        file.write(buffer + "\n")

def FolderInit(path):
    if not PathExist(path):
        os.makedirs(path)

def Auth(acc, psw):
    sess = requests.session()
    resp = sess.post("https://course.nuk.edu.tw/Sel/SelectMain1.asp", {"Account": acc, "Password": psw})
    resp.encoding = "big5"
    info = bs4.BeautifulSoup(resp.text, "lxml")
    if info.b.text == "帳號、密碼有誤，請確認後再重新登入！":
        logger("A failed login.")
        return None
    return sess

PathExist = lambda path: os.path.exists(path)
incoming = lambda req: logger("Incoming connection from {0}, target page {1}".format(req.remote_addr, req.path), 1)
# ----- End of Functions -----

# ----- Flask Programs -----
app = Flask(__name__, static_folder='templates/static', 
template_folder='templates', )
secret = db.get(query.secret.exists())
if secret == None: secret = os.urandom(24).hex() ; db.insert({"secret": secret})
else: secret = secret["secret"]
app.config['SECRET_KEY'] = secret
CSRFProtect(app)

@app.route("/")
def Root():
    incoming(request)
    if session.get("login"):
        return render_template("index.html", Version = "1.0.0")
    logger("Not login! Redirect to Login page")
    return redirect(url_for("login"))

@app.route("/login", methods=['GET', 'POST'])
def login():
    incoming(request)
    if request.method == "GET":
        if session.get("login"):
            return redirect(url_for("Root"))
    else:
        data = request.form
        if data.get("acc") and data.get("psw"):
            #Auth
            if Auth(data["acc"], data["psw"]): 
                session["acc"] = data["acc"]
                session["psw"] = data["psw"]
                session["login"] = "Yes"
                return redirect(url_for("Root"))
            return "Invaild Login Informations"
    return render_template("login.html")

@app.route("/logout/")
def logout():
    incoming(request)
    session.pop("acc", None)
    session.pop("psw", None)
    session.pop("login", None)
    return redirect(url_for("Root"))

@app.route("/WIP")
def classes():
    incoming(request)
    return "WIP"

@app.route("/classes")
def classView():
    incoming(request)
    if session.get("login"):
        sess = Auth(session["acc"], session["psw"])
        resp = sess.get("https://course.nuk.edu.tw/Sel/roomlist1.asp")
        resp.encoding = "big5"
        info = bs4.BeautifulSoup(resp.text, "lxml")
        classes = info.table
        classes["class"] = "w3-table w3-striped w3-border w3-gray"
        classes.tr["class"] = "w3-green"
        classes["style"] = None
        for i in classes.find_all("tr")[1:]:
            for o in i.find_all("td")[:2]:
                o["class"] = "w3-green"
            for o in i.find_all("td")[2:]:
                if o.string == None and str(o.contents[-1]) != "<br/>":
                    for j in Codes.items():
                        o.contents[-1].replace_with(o.contents[-1].replace(j[0], j[1]))
                    temp = o.contents[-1].split(",")
                    if len(temp) > 1:
                        o.contents[-1].replace_with(temp[0])
                        for j in temp[1:]:
                            o.contents.append(info.new_tag("br"))
                            o.contents.append(info.new_string(j))
        return render_template("class.html", Version = "1.0.0", Tables = classes, ContentAttri = "id='ClassesContent'")
    logger("Not login! Redirect to Login page")
    return redirect(url_for("login"))

app.run(host = "0.0.0.0", port = "9487", ssl_context=("../../Certs/cert.pem", "../../Certs/privkey.pem"))

# ----- End of Flask -----
