from flask import Flask, request, render_template, session, redirect, url_for
from markupsafe import escape
from flask_wtf.csrf import CSRFProtect
from datetime import datetime, time
from tinydb import TinyDB, Query
import requests, bs4, os, pytz

from config import *

class TDB():
    def __init__(self):
        self.db = TinyDB("db.tinydb")
    def Save(self):
        self.db.close()
        self.db = TinyDB("db.tinydb")

tinydb = TDB()
query = Query()
tw = pytz.timezone('Asia/Taipei')
d_start = datetime(2020,9,14,0,0,0,0,tw)


#Logger file path
Log = str(datetime.now(tw))[:-7].replace(" ", "_").replace(":","_") + ".log"
# ----- Functions -----
def gen_checkbox(id, week, holder, value):
    return '<dd><label for="{0}">第{1}周</label><input type="checkbox" id="{0}" class="w3-check checkbox" {4}/><input name="{0}" class="w3-input w3-border" type="text" placeholder="{2}" value="{5}" {3}></dd>'.format(id, week, holder, "" if value else "disabled", "checked" if value else "", value)

#Compare if the time is between two time object
TimeCompare = lambda obj, val: obj[0] < val and val < obj[1]

#Get the week since started classes
getWeek = lambda: str(((datetime.now(tw) - d_start).days // 7) + 1)

#Check exist path
PathExist = lambda path: os.path.exists(path)

#Connection message
incoming = lambda req: logger("Incoming connection from {0}, target page {1}".format(req.remote_addr, req.path), 1)

#Get all class datas
def Classdata(sess):
    resp = sess.get("https://course.nuk.edu.tw/Sel/query3.asp")
    resp.encoding = "big5"
    info = bs4.BeautifulSoup(resp.text, "lxml")
    classes = [[o.string for o in i.find_all("td")] for i in info.table.find_all("tr")[1:]]
    return {i[1]:i for i in classes if i[9] == "選上"}

#Log Messages
def logger(msg, code = 0):
    #0 to 4 are available
    FolderInit(LoggerPath)
    with open(LoggerPath + Log, "a+", encoding='UTF-8') as file:
        buffer = "{0} | {1} : {2}".format(types[code], datetime.now(tw), msg)
        print(buffer)
        file.write(buffer + "\n")

#Init a Path Folder
def FolderInit(path):
    if not PathExist(path):
        os.makedirs(path)

#Translate classroom
def RoomTranslate(room):
    for j in Codes.items():
        room = room.replace(j[0], j[1])
    return room

#Login to class selection system and get Session
def Auth(acc, psw):
    sess = requests.session()
    resp = sess.post("https://course.nuk.edu.tw/Sel/SelectMain1.asp", {"Account": acc, "Password": psw})
    resp.encoding = "big5"
    info = bs4.BeautifulSoup(resp.text, "lxml")
    if info.b.text == "帳號、密碼有誤，請確認後再重新登入！":
        logger("A failed login.")
        return None
    session["acc"] = acc
    session["psw"] = psw
    session["login"] = "Yes"
    #Also init any classes that don't have datas
    datas = Classdata(sess)
    for i in datas.items():
        if not tinydb.db.get(query[session["acc"]][i[0]].exists()):
            tinydb.db.insert({session["acc"] : {i[0]: {"weeks": max_week}}})
            room = i[1][6].split(",")[0].strip()
            if room == "": room = "無標記教室"
            for o in range(1, max_week + 1):
                room = RoomTranslate(room)
                tinydb.db.insert({session["acc"]:{i[0]: {"room" + str(o): room}}})
    return sess
# ----- End of Functions -----

# ----- Flask Programs -----
app = Flask(__name__, static_folder='templates/static', 
template_folder='templates', )
#Secret generating and saving
secret = tinydb.db.get(query.secret.exists())
if secret == None: secret = os.urandom(24).hex() ; tinydb.db.insert({"secret": secret})
else: secret = secret["secret"]
app.config['SECRET_KEY'] = secret
#CSRF Protect for flask
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

#Planning to remove in final state
@app.route("/WIP")
def classes():
    incoming(request)
    return "WIP"

@app.route("/classes")
def classView():
    incoming(request)
    if session.get("login"):
        sess = Auth(session["acc"], session["psw"])
        if sess:
            resp = sess.get("https://course.nuk.edu.tw/Sel/roomlist1.asp")
            resp.encoding = "big5"
            info = bs4.BeautifulSoup(resp.text, "lxml")
            classes = info.table
            classes["class"] = "w3-table w3-striped w3-border w3-gray"
            classes["style"] = None
            classes.tr["class"] = "w3-green"
            data = Classdata(sess)
            weeknow = int(getWeek())
            for i in classes.find_all("tr")[1:]:
                for o in i.find_all("td")[:2]:
                    o["class"] = "w3-green"
                k = 0
                for o in i.find_all("td")[2:]:
                    #All classes
                    day = str((weeknow + 1) if k < datetime.now(tw).weekday() else weeknow)
                    classid = o.contents[0].string
                    weeks = tinydb.db.get(query[session["acc"]][classid].weeks.exists())
                    if weeks: weeks = weeks[session["acc"]][classid]["weeks"]
                    else: weeks = max_week
                        
                    if str(o.contents[-1]) != "<br/>":
                        #Classes that has room
                        room = tinydb.db.get(query[session["acc"]][classid]["room" + day].exists())
                        if room:
                            room = room[session["acc"]][classid]["room" + day]
                            o.contents[-1].replace_with(RoomTranslate(o.contents[-1]))
                            temp = [i for i in o.contents[-1].split(",") if i != room]
                            o.contents[-1].replace_with(room)
                            if len(temp) > 1:
                                temp[0] = "(" + temp[0] ; temp[-1] = temp[-1] + ")"
                                for j in temp:
                                    if room: o.contents.append(info.new_tag("br"))
                                    else: room = True
                                    o.contents.append(info.new_string(j))
                            elif len(temp) == 1:
                                if room: o.contents.append(info.new_tag("br"))
                                o.contents.append(info.new_string("(%s)" % temp[0]))
                            data[classid][6] = "<br>".join([str(i) for i in o.contents[3:] if str(i) != "<br/>"]).strip()
                        else: 
                            o.contents = []
                            if data.get(classid): data[classid][6] = ""
                    else:
                        room = tinydb.db.get(query[session["acc"]][classid]["room" + day].exists())
                        if room:
                            room = room[session["acc"]][classid]["room" + day]
                            o.contents.append(info.new_string(room))
                            data[classid][6] = room
                        else: 
                            o.contents = []
                            if data.get(classid): data[classid][6] = ""
                    k = (k+1) % 7
            schedule = {i[1]:i[5] for i in data.values()}
            week = datetime.now(tw).weekday()
            now_time = datetime.now(tw).time()
            nextID = stat = start = None # - stat - : 0 = before, 1 = in class
            begin = week 
            while not nextID:
                for i in sorted([i for i in schedule.items() if Date[week] in i[1]], key=lambda x: x[1]):
                    for o in [o for o in Timer.items() if str(o[0]) in i[1]]:
                        if ((TimeCompare(o[1], now_time) or now_time < o[1][0] or begin != week) and data[i[0]][6]):
                            nextID = i[0]
                            stat = 0 if now_time < o[1][0] else 1
                            start = o[1][0] if now_time < o[1][0] or week != begin else o[1][1]
                            break 
                    if nextID: break
                if nextID: break
                week = ( week + 1 ) % 7
                if week == begin: break
            note = tinydb.db.get(query[session["acc"]][nextID]["note" + str((weeknow + 1) if week < begin else weeknow)].exists())
            if note: note = note[session["acc"]][nextID]["note" + str((weeknow + 1) if week < begin else weeknow)]
            nextclass = ("下" if week < begin else "本") + ((("周{3}{0}下課<br>正在上{1}" if stat and begin == week else "周{3}{0}上課<br>下堂課是{1}") + "<br>位於{2}").format(start.strftime("%H點%M分") ,data[nextID][2], data[nextID][6], Date[week]) + (("<br>備註：%s" % note) if note else "")) if nextID else "無匹配課程...?!"
            return render_template("class.html", Version = "1.0.0", Tables = classes, ContentAttri = "id='ClassesContent'", week=str(weeknow), NextClass=nextclass)
    logger("Not login! Redirect to Login page")
    return redirect(url_for("login"))

@app.route("/manage", methods=['GET', 'POST'])
def Manager():
    incoming(request)
    if session.get("login"):
        if request.method == "GET":
            sess = Auth(session["acc"], session["psw"])
            if sess:
                resp = sess.get("https://course.nuk.edu.tw/Sel/query3.asp")
                resp.encoding = "big5"
                info = bs4.BeautifulSoup(resp.text, "lxml")
                classes = info.table
                del classes["style"], classes["border"]
                classes["class"] = "w3-table w3-striped w3-gray"
                classes.tr["class"] = "w3-red"
                for i in classes.find_all("tr")[1:]:
                    if i.find_all("td")[-1].string == "選上":
                        button = info.new_tag("input")
                        button["type"] = "submit" ; button["class"] = "w3-button w3-green"
                        button["name"] = "ClassID" ; button["value"] = i.find_all("td")[1].string
                        i.find_all("td")[1].string.replace_with(button)
                    else: del i
                return render_template("classlist.html", Version = "1.0.0", Classlist = classes, week=getWeek())
        else:
            data = request.form
            if data.get("ClassID") and session.get("login"):
                return redirect(url_for("EditClass", classID = data["ClassID"]))
            return "Where is your 'ClassID'?"
    logger("Not login! Redirect to Login page")
    return redirect(url_for("login"))

@app.route("/manage/<string:classID>", methods=['GET', 'POST'])
def EditClass(classID):
    if session.get("login"):
        classID = escape(classID)
        if request.method == "GET":
            sess = Auth(session["acc"], session["psw"])
            weeks = tinydb.db.get(query[session["acc"]][classID].weeks.exists())
            if sess and weeks:
                datas = Classdata(sess)
                weeks = weeks[session["acc"]][classID]["weeks"]
                classrooms = classinfos = ""
                for i in range(1,weeks+1):
                    room = tinydb.db.get(query[session["acc"]][classID]["room" + str(i)].exists())
                    note = tinydb.db.get(query[session["acc"]][classID]["note" + str(i)].exists())
                    checked = bool(room)
                    if room: room = room[session["acc"]][classID]["room" + str(i)]
                    else: room = ""
                    if note: note = note[session["acc"]][classID]["note" + str(i)]
                    else: note = ""
                    classrooms += gen_checkbox("room"+str(i), i, "教室位置", room)
                    classinfos += gen_checkbox("note"+str(i), i, "備註", note)
                return render_template("manage.html", Version = "1.0.0", classID = classID, className = datas[classID][2], teacher=datas[classID][7], ContentAttri = "id = 'manage'", week=getWeek(), ClassRooms=classrooms, ClassInfos=classinfos, totalweeks=weeks)
        else:
            data = request.form
            weeks = data.get("weeks")
            if not weeks or not(int(weeks) in range(1, max_week+1)): weeks = max_week
            else: weeks = int(weeks)
            tinydb.db.remove(query[session["acc"]][classID].exists())
            tinydb.db.insert({session["acc"] : {classID: {"weeks": weeks}}})
            for i in range(1, weeks+1):
                room = data.get("room" + str(i))
                note = data.get("note" + str(i))
                if room: tinydb.db.insert({session["acc"]:{classID: {"room" + str(i): room}}})
                if note: tinydb.db.insert({session["acc"]:{classID: {"note" + str(i): note}}})
            tinydb.Save()
            return redirect(url_for("EditClass", classID = classID))
    logger("Not login! Redirect to Login page")
    return redirect(url_for("login"))

if ssl: app.run(host = "0.0.0.0", port = "9487", ssl_context = ssl)
else: app.run(host = "0.0.0.0", port = "9487")

# ----- End of Flask -----
