from flask import Flask, request, render_template, session, redirect, url_for
from markupsafe import escape
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
import pytz
from tinydb import TinyDB, Query
import requests, bs4, os

from config import *

db = TinyDB("db.tinydb")
query = Query()
tw = pytz.timezone('Asia/Taipei')
d_start = datetime(2020,9,14,0,0,0,0,tw)
max_week = 18

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
def gen_checkbox(id, week, holder, value):
    return '<dd><label for="{0}">第{1}周</label><input type="checkbox" id="{0}" class="w3-check checkbox" {4}/><input name="{0}" class="w3-input w3-border" type="text" placeholder="{2}" value="{5}" {3}></dd>'.format(id, week, holder, "" if value else "disabled", "checked" if value else "", value)

def getWeek():
    return str(((datetime.now(tw) - d_start).days // 7) + 1)

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
        return render_template("index.html", Version = "1.0.0", week=getWeek())
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
    return render_template("login.html", week=getWeek())

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
                #All classes
                if o.string == None:
                    classid = o.contents[0].string
                    weeks = db.get(query[session["acc"]][classid].weeks.exists())
                    if weeks: weeks = weeks[session["acc"]][classid]["weeks"]
                    else: db.insert({session["acc"] : {classid: {"weeks": max_week}}}) ; weeks = max_week
                    if int(getWeek()) <= weeks:
                        if str(o.contents[-1]) != "<br/>":
                            #Classes that has room
                            for j in Codes.items():
                                o.contents[-1].replace_with(o.contents[-1].replace(j[0], j[1]))
                            temp = o.contents[-1].split(",")
                            room = db.get(query[session["acc"]][classid]["room" + getWeek()].exists())
                            if room: room = room[session["acc"]][classid]["room" + getWeek()]
                            else: room = ""
                            o.contents[-1].replace_with(room)

                            if len(temp) > 1:
                                temp[0] = "(" + temp[0]
                                temp[-1] = temp[-1] + ")"
                                for j in temp:
                                    if room: o.contents.append(info.new_tag("br"))
                                    else: room = True
                                    o.contents.append(info.new_string(j))
                            else:
                                if room != temp[0]:
                                    if room: o.contents.append(info.new_tag("br"))
                                    o.contents.append(info.new_string("(%s)" % temp[0]))
                    else:
                        o.contents = []
                    
        return render_template("class.html", Version = "1.0.0", Tables = classes, ContentAttri = "id='ClassesContent'", week=getWeek())
    logger("Not login! Redirect to Login page")
    return redirect(url_for("login"))

@app.route("/manage", methods=['GET', 'POST'])
def Manager():
    incoming(request)
    if session.get("login"):
        if request.method == "GET":
            sess = Auth(session["acc"], session["psw"])
            resp = sess.get("https://course.nuk.edu.tw/Sel/query3.asp")
            resp.encoding = "big5"
            info = bs4.BeautifulSoup(resp.text, "lxml")
            classes = info.table
            del classes["style"]
            del classes["border"]
            classes["class"] = "w3-table w3-striped w3-gray"
            classes.tr["class"] = "w3-red"
            for i in classes.find_all("tr")[1:]:
                if i.find_all("td")[-1].string != "選上": del i
                else:
                    button = info.new_tag("input")
                    button["type"] = "submit" ; button["class"] = "w3-button w3-green" ; button["name"] = "ClassID" ; button["value"] = i.find_all("td")[1].string
                    i.find_all("td")[1].string.replace_with(button)
            return render_template("classlist.html", Version = "1.0.0", Classlist = classes, week=getWeek())
        else:
            data = request.form
            if data.get("ClassID") and session.get("login"):
                return redirect(url_for("EditClass", classID = data["ClassID"]))
    else:
        logger("Not login! Redirect to Login page")
        return redirect(url_for("login"))
    return render_template("index.html", Version = "1.0.0", week=getWeek())

@app.route("/manage/<string:classID>", methods=['GET', 'POST'])
def EditClass(classID):
    if session.get("login"):
        classID = escape(classID)
        if request.method == "GET":
            sess = Auth(session["acc"], session["psw"])
            if sess:
                resp = sess.get("https://course.nuk.edu.tw/Sel/query3.asp")
                resp.encoding = "big5"
                info = bs4.BeautifulSoup(resp.text, "lxml")
                classes = [[o.string for o in i.find_all("td")] for i in info.table.find_all("tr")[1:]]
                datas = {i[1]:i for i in classes}
                weeks = db.get(query[session["acc"]][classID].weeks.exists())
                if weeks: weeks = weeks[session["acc"]][classID]["weeks"]
                else: db.insert({session["acc"] : {classID: {"weeks": max_week}}}) ; weeks = max_week
                classrooms = ""
                classinfos = ""
                for i in range(1,weeks+1):
                    room = db.get(query[session["acc"]][classID]["room" + str(i)].exists())
                    note = db.get(query[session["acc"]][classID]["note" + str(i)].exists())
                    checked = bool(room)
                    if room: room = room[session["acc"]][classID]["room" + str(i)]
                    else: 
                        room = datas[classID][6].split(",")[0]
                        for o in Codes.items():
                            room = room.replace(o[0], o[1])
                    if note: note = note[session["acc"]][classID]["note" + str(i)]
                    else: note = ""
                    classrooms += gen_checkbox("room"+str(i), i, "教室位置", room)
                    classinfos += gen_checkbox("note"+str(i), i, "備註", note)
                return render_template("manage.html", Version = "1.0.0", classID = classID, className = datas[classID][2], teacher=datas[classID][7], ContentAttri = "id = 'manage'", week=getWeek(), ClassRooms=classrooms, ClassInfos=classinfos, totalweeks=weeks)
        else:
            data = request.form
            weeks = data.get("weeks")
            if not weeks: weeks = max_week
            else: weeks = int(weeks)
            db.remove(query[session["acc"]][classID].exists())
            db.insert({session["acc"] : {classID: {"weeks": weeks}}})
            for i in range(1, weeks+1):
                room = data.get("room" + str(i))
                note = data.get("note" + str(i))
                if room: db.insert({session["acc"]:{classID: {"room" + str(i): room}}})
                if note: db.insert({session["acc"]:{classID: {"note" + str(i): note}}})
                
            return redirect(url_for("EditClass", classID = classID))
    logger("Not login! Redirect to Login page")
    return redirect(url_for("login"))
if ssl: app.run(host = "0.0.0.0", port = "9487", ssl_context = ssl)
else: app.run(host = "0.0.0.0", port = "9487")

# ----- End of Flask -----
