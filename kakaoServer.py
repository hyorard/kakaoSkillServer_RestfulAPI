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
def makeGraph(x,y,type):
    if type == "cur":
        plt.plot(x,y,'g')
        plt.xlabel("time")
        plt.ylabel("number of people")
        plt.title("Congestion of recent 1 hour")
    elif type == "avg":
        plt.plot(x,y,'b')
        plt.xlabel("time")
        plt.ylabel("average number of people")
        plt.title("Average Congestion")
    fig = plt.gcf()
    fig.savefig("vis.png")

### 그래프 그리기 위한 그래프 x,y 축 값 추출 후 반환 ###
def curVisualization():
    conn.commit()
    sql = """SELECT time FROM currentAnalysis ORDER BY time DESC limit 12"""
    c.execute(sql)
    time = c.fetchall()
    tmp = [v[0] for v in time]
    x = [str(v.hour)+"-"+str(v.minute) for v in tmp]
    x.reverse()
    #이런 식으로 저장됨
    #x = ['13-48', '13-48', '13-48', '13-49', '13-58', '13-59', '14-0', '14-1', '17-40', '17-50', '18-30', '18-30']

    conn.commit()
    sql = """SELECT result FROM currentAnalysis ORDER BY time DESC limit 12"""
    c.execute(sql)
    res = c.fetchall()
    y = [v[0] for v in res]
    y.reverse()
    #이런 식으로 저장됨
    #y = [None, None, None, None, None, None, None, None, None, 2, None, 2] #현재 None 값 때문에 임의로 y 설정
    y = [3,5,2,1,7,8,9,2,3,4,6,1]

    return (x,y)

### 그래프 그리기 위한 그래프 x,y 축 값 추출 후 반환 ###
def avgVisualization(target):
    #유저가 요청한 시간 앞 3시간치
    conn.commit()
    sql = """SELECT hour,result FROM averageAnalysis WHERE hour < (%s) ORDER BY hour desc limit 3"""
    c.execute(sql,(target,))
    avgList = c.fetchall()
    avgList = list(avgList).reverse()
    #유저가 요청한 시간대
    conn.commit()
    sql = """SELECT hour,result FROM averageAnalysis WHERE hour = (%s)"""
    c.execute(sql,(tartget,))
    avgList += c.fetchall()
    dbResult = avgList[-1]
    #유저가 요청한 시간 뒤 3시간치
    conn.commit()
    sql = """SELECT hour,result FROM averageAnalysis WHERE hour > (%s) ORDER BY hour asc limit 3"""
    c.execute(sql,(target,))
    avgList += c.fetchall()
    
    x = [v[0] for v in avgList]
    y = [v[1] for v in avgList]

    return (x,y,dbResult)

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
    conn.commit()
    sql = """SELECT result FROM currentAnalysis ORDER BY time DESC limit 1"""
    c.execute(sql)
    dbResult = c.fetchone()[0]
    #DB에 유저 정보 삽입
    conn.commit()
    sql = """INSERT INTO customerKakao (id, requestTime) VALUES (%s,%s)"""
    c.execute(sql,(userId,reqTime))
    conn.commit()

    """ 시각화 """
    x,y = curVisualization()
    makeGraph(x,y,"cur")

    #이상치 제거 및 응답 전송
    if(dbResult == None):
        text = "현재 분석이 불가능하니 잠시만 기다려주세요!"
        data = {"version": "2.0","template":{"outputs":[{"simpleText":{"text":text}}]}}
    else:
        title = "현재 공간에는 " + str(dbResult) + "명이 있습니다!" 
        description = "위 그래프는 최근 한 시간 혼잡도 분석 결과입니다!\n" 
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

    x,y,dbResult = avgVisualization(target)
    makeGraph(x,y,"avg")


    #이상치 제거
    if(dbResult == None):
        text = "현재 분석이 불가능하니 잠시만 기다려주세요!"
        data = {"version": "2.0","template":{"outputs":[{"simpleText":{"text":text}}]}}
    else:
        title = "이 시간대에는 평균 " + str(dbResult) + "명이 있습니다!" 
        description = "위 그래프는 현재 기준 전,후 3시간 동안의 평균 혼잡도 분석 결과입니다!\n" 
        url = "http://110.34.109.166:4967/getGraph"
        data = {"version": "2.0","template": {"outputs":[{"basicCard":{"title":title,"description":description,"thumbnail":{"imageUrl":url,"fixedRatio":"true","width":"640","height":"480"}}}]}}

    #응답 전송
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
