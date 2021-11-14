from datetime import time, datetime
import pytz
# --- Change this to setting the school begin date
tw = pytz.timezone('Asia/Taipei')
d_start = datetime(2021,9,22,0,0,0,0,tw)
# --- Don't change below if you don't know what you doing. ---
#Log type
types = ["Info", "Warning", "Critical", "Success", "Failed"]
#Path to save logs
LoggerPath = "Logs/"
#ssl = ("../Certs/cert.pem", "../Certs/privkey.pem")
ssl = None
#Limit of weeks in a class
max_week = 18

#Building name of each classrooms
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

#Time of classes
Timer = {
    "X":[time(7, 5), time(7, 55)], #早7
    1:[time(8, 5), time(8, 55)],
    2:[time(9, 5), time(9, 55)],
    3:[time(10, 10), time(11, 0)],
    4:[time(11, 10), time(12, 0)],
    "Y":[time(12, 10), time(13, 0)], #午休
    5:[time(13, 10), time(14, 0)],
    6:[time(14, 10), time(15, 0)],
    7:[time(15, 15), time(16, 5)],
    8:[time(16, 20), time(17, 10)],
    9:[time(17, 20), time(18, 10)],
    10:[time(18, 20), time(19, 10)],
    11:[time(19, 15), time(20, 5)],
    12:[time(20, 10), time(21, 0)],
    13:[time(21, 5), time(21, 55)]
    }

#Date to integer, program needed, please don't touch dis-
Date = list("一二三四五六日")
