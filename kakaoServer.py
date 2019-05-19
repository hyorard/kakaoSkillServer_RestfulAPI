from flask import Flask,jsonify,make_response,json,request,send_file
from collections import OrderedDict
import MySQLdb
import datetime
import matplotlib.pyplot as plt


### DB 접속 ###
conn = MySQLdb.connect(host='127.0.0.1', port=3306, database='hufsCongestion', user='root', passwd='hufscongestion')
c = conn.cursor()

### Flask Server Setting ###
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

### HTTP 응답 전송 함수 ###
def makeResponse(data):
    data = jsonify(data)
    resp = make_response(data)
    resp.status_code = 200
    resp.mimetype="application/json"
    return resp

### 분석 그래프 생성. 현재 디렉토리 "vis.png" ###
def makeGraph(x,y):
    plt.plot(x,y,'g')
    plt.xlabel("time")
    plt.ylabel("number of people")
    plt.title("Congestion of recent 1 hour")
    fig = plt.gcf()
    fig.savefig("vis.png")

### 최근 한 시간의 데이터 fetch ###
def curVisualization():
    sql = """SELECT time FROM currentAnalysis ORDER BY time DESC limit 12"""
    c.execute(sql)
    time = c.fetchall()
    tmp = [v[0] for v in time]
    x = [str(v.hour)+"-"+str(v.minute) for v in tmp]
    x.reverse()
    #x = ['13-48', '13-48', '13-48', '13-49', '13-58', '13-59', '14-0', '14-1', '17-40', '17-50', '18-30', '18-30']

    sql = """SELECT result FROM currentAnalysis ORDER BY time DESC limit 12"""
    c.execute(sql)
    res = c.fetchall()
    y = [v[0] for v in res]
    y.reverse()
    #y = [None, None, None, None, None, None, None, None, None, 2, None, 2] #현재 None 값 때문에 임의로 y 설정
    y = [3,5,2,1,7,8,9,2,3,4,6,1]

    return (x,y)

@app.route("/getGraph",methods=['GET','POST'])
def getGraph():
    filename = "vis.png"
    return send_file(filename, mimetype="image/gif")

### 현재혼잡도 분석값 응답 ###
@app.route("/get/curApple",methods=['GET','POST'])
def curApple():

    kakaoReq = request.json

    #요청한 유저 정보 추출
    #userId = kakaoReq["userRequest"]["user"]["id"] #배포용
    userId = "test getCurApple" #테스트용
    reqTime = datetime.datetime.now()



    """ 분석값 """
    #DB에 가장 최근 분석값 요청
    sql = """SELECT result FROM currentAnalysis ORDER BY time DESC limit 1"""
    c.execute(sql)
    dbResult = c.fetchone()[0]
    #DB에 유저 정보 삽입
    sql = """INSERT INTO customerKakao (id, requestTime) VALUES (%s,%s)"""
    c.execute(sql,(userId,reqTime))
    conn.commit()

    """ 시각화 """
    x,y = curVisualization()
    makeGraph(x,y)

    #이상치 제거 및 응답 전송
    if(dbResult == None):
        text = "현재 분석이 불가능하니 잠시만 기다려주세요!"
        data = {"version": "2.0","template":{"outputs":[{"simpleText":{"text":text}}]}}
    else:
        title = "현재 혼잡도 및 최근 한 시간 혼잡도입니다!"
        description = "위 그래프는 최근 한 시간 혼잡도 분석 결과입니다!\n현재 공간에는 " + str(dbResult) + "명이 있습니다!" 
        url = "http://110.34.109.166:4967/getGraph"
        data = {"version": "2.0","template": {"outputs":[{"basicCard":{"title":title,"description":description,"thumbnail":{"imageUrl":url,"fixedRatio":"true","width":"640","height":"480"}}}]}}


    resp = makeResponse(data)
    return resp


### 평균혼잡도 분석값 응답 ###
@app.route("/get/avgApple",methods=['GET','POST'])
def avgApple():

    kakaoReq = request.json

    #요청한 유저 정보 추출
    #userId = kakaoReq["userRequest"]["user"]["id"] #배포용
    userId = "test getAvgApple" #테스트용
    reqTime = datetime.datetime.now()

    #유저가 요청한 시간대 추출
    target = reqTime.hour

    
    #DB에 요청한 시간대 평균 분석값 요청
    sql = """SELECT result FROM averageAnalysis WHERE hour = (%s)"""
    c.execute(sql, (target,))
    dbResult = c.fetchone()
    #dbResult = c.fetchall()??
    #DB에 유저 정보 삽입
    sql = """INSERT INTO customerKakao (id, requestTime) VALUES (%s,%s)"""
    c.execute(sql,(userId,reqTime))
    conn.commit()

    #이상치 제거
    if(dbResult == None):
        text = "현재 서비스 시간이 아닙니다. 서비스 시간은 09:00 - 22:00 입니다."
    else:
        text = "최근 일주일 간 이 시간대에 평균" + str(dbResult) + "명이 있었습니다."

    #응답 전송
    data = {"version": "2.0","template":{"outputs":[{"simpleText":{"text":text}}]}}
    resp = makeResponse(data)
    return resp

### 한산한 시간대 분석값 응답 ###
@app.route("/get/timeAnal",methods=['GET','POST'])
def timeAnal():

    kakaoReq = request.json

    #요청한 유저 정보 추출
    #userId = kakaoReq["userRequest"]["user"]["id"] #배포용
    userId = "test getTimeAnal" #테스트용
    reqTime = datetime.datetime.now()

    #DB 연동 1,2,3,4,5주전 결과 값을 들고 와야 함. DB에서 그렇게 긁어 오는 법을 알아내야 함. 긁어와서 언제가 한산한지 보내기만 하면 됨.

    sql = """SELECT requestTime FROM customerKakao WHERE requestTime >= DATE_ADD(NOW(), INTERVAL -1 WEEK)"""
    c.execute(sql)
    dbResult = c.fetchone()[0]
    sql = """INSERT INTO customerKakao (id, requestTime) VALUES (%s,%s)"""
    c.execute(sql,(userId,reqTime))
    conn.commit()



    text = "한산한 시간대 분석 기능은 현재 업데이트 예정 기능입니다!"
    data = {"version": "2.0","template":{"outputs":[{"simpleText":{"text":text}}]}}
    resp = makeResponse(data)
    return resp

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=4967)
