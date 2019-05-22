from flask import Flask,jsonify,make_response,json,request,send_file
from collections import OrderedDict
import MySQLdb
import datetime
import matplotlib.pyplot as plt
import time
import random





"""#1                       스킬 서버 준비                          """

### DB 접속 ###
conn = MySQLdb.connect(host='127.0.0.1', port=3306, database='hufsCongestion', user='root', passwd='hufscongestion')
c = conn.cursor()

### set Flask Server and run it ###
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

### HTTP 응답 전송 함수 ###
def makeResponse(data):
    data = jsonify(data)
    resp = make_response(data)
    resp.status_code = 200
    resp.mimetype="application/json"
    return resp







"""                             여기서부터                              """
"""#2                           시각화 전처리                           """

### 그래프 그리기 위한 그래프 x,y 축 값 추출 후 반환 ###
def curVisualization():
    conn.commit()
    sql = """SELECT time FROM currentAnalysis ORDER BY time DESC limit 12"""
    c.execute(sql)
    DBtime = c.fetchall()
    tmp = [v[0] for v in DBtime]
    #time = [str(v.hour)+"-"+str(v.minute) for v in tmp]
    time = ["{0}-{1}".format(v.hour,v.minute) for v in tmp]
    time.reverse()
    #이런 식으로 저장됨
    #x = ['13-48', '13-48', '13-48', '13-49', '13-58', '13-59', '14-0', '14-1', '17-40', '17-50', '18-30', '18-30']

    conn.commit()
    sql = """SELECT result FROM currentAnalysis ORDER BY time DESC limit 12"""
    c.execute(sql)
    res = c.fetchall()
    nHuman = [v[0] for v in res]
    nHuman.reverse()
    #이런 식으로 저장됨
    #y = [None, None, None, None, None, None, None, None, None, 2, None, 2] #현재 None 값 때문에 임의로 y 설정
    nHuman = [3,5,2,1,7,8,9,2,3,4,6,1]

    return (time,nHuman)


### 그래프 그리기 위한 그래프 x,y 축 값 추출 후 반환 ###
def avgVisualization(target):
    #유저가 요청한 시간 앞 3시간치
    avgList = tuple()
    conn.commit()
    sql = """SELECT hour,result FROM averageAnalysis WHERE hour < (%s) ORDER BY hour desc limit 3"""
    c.execute(sql,(target,))
    avgList = c.fetchall()
    avgList = list(avgList)
    avgList.reverse()

    #유저가 요청한 시간대
    conn.commit()
    sql = """SELECT hour,result FROM averageAnalysis WHERE hour = (%s)"""
    c.execute(sql,(target,))
    avgList += c.fetchall()
    dbResult = avgList[-1][1]

    #유저가 요청한 시간 뒤 3시간치
    conn.commit()
    sql = """SELECT hour,result FROM averageAnalysis WHERE hour > (%s) ORDER BY hour asc limit 3"""
    c.execute(sql,(target,))
    avgList += c.fetchall()

    hour = ["{0}".format(v[0]) for v in avgList]
    nHuman = [v[1] for v in avgList]

    return (hour,nHuman,dbResult)


### 한산한 시간대 그래프 그리기 위한 그래프 x,y 축 값 추출 후 반환 ###
def quietVisualization():
    conn.commit()
    sql = """ SELECT hour,result FROM averageAnalysis ORDER BY result asc limit 6"""
    c.execute(sql)
    Tquiet = c.fetchall()

    hour = ["{0}".format(v[0]) for v in Tquiet]
    nHuman = [v[1] for v in Tquiet]
    dbResult = [time for time in hour][:3]

    return (hour,nHuman,dbResult)





"""#3                           시각화                          """

### 분석 그래프 생성. 현재 디렉토리 "vis.png" ###
def makeGraph(x,y,type):
    plt.clf()

    if type == "cur":
        plt.plot(x,y,'g')
        plt.xlabel("time")
        plt.ylabel("number of people")
        plt.title("Congestion of recent 1 hour")
        cur = plt.gcf()
        cur.savefig("cur.png")
    elif type == "avg":
        plt.plot(x,y,'b')
        plt.xlabel("time")
        plt.ylabel("average number of people")
        plt.title("Average Congestion")
        avg = plt.gcf()
        avg.savefig("avg.png")
    elif type == "qtt":
        plt.plot(x,y,'y')
        plt.xlabel("time")
        plt.ylabel("average number of people")
        plt.title("Most 6 Quiet Time")
        avg = plt.gcf()
        avg.savefig("qtt.png")









"""                 여기서부터                  """
"""#4                 라우팅                    """


@app.route("/getGraph/avg/<int:forUpdate>",methods=['GET','POST'])
def getAvgGraph(forUpdate):
    time.sleep(1)
    filename2 = "avg.png"
    return send_file(filename2, as_attachment=True,mimetype="image/gif")


@app.route("/getGraph/cur/<int:forUpdate>",methods=['GET','POST'])
def getCurGraph(forUpdate):
    time.sleep(1)
    filename = "cur.png"
    return send_file(filename, as_attachment=True,mimetype="image/gif")

@app.route("/getGraph/qtt/<int:forUpdate>",methods=['GET','POST'])
def getQttGraph(forUpdate):
    time.sleep(1)
    filename = "qtt.png"
    return send_file(filename, as_attachment=True,mimetype="image/gif")

### 현재혼잡도 분석값 응답 ###
@app.route("/get/curApple",methods=['GET','POST'])
def curApple():

    kakaoReq = request.json

    #요청한 유저 정보 추출
    userId = kakaoReq["userRequest"]["user"]["id"] #배포용
    #userId = "test getCurApple" #테스트용
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
        title = "현재 공간에는 {0}명이 있습니다.".format(dbResult)
        description = "위 그래프는 최근 한 시간 \n혼잡도 분석 결과입니다.\n"
        url = "http://110.34.109.166:4967/getGraph/cur/{0}".format(random.randint(1,1000))
        data = {"version": "2.0","template": {"outputs":[{"basicCard":{"title":title,"description":description,"thumbnail":{"imageUrl":url,"fixedRatio":"true","width":"640","height":"480"}}}]}}


    resp = makeResponse(data)
    return resp


### 평균혼잡도 분석값 응답 ###
@app.route("/get/avgApple",methods=['GET','POST'])
def avgApple():

    kakaoReq = request.json

    #요청한 유저 정보 추출
    userId = kakaoReq["userRequest"]["user"]["id"] #배포용
    #userId = "test getAvgApple" #테스트용
    reqTime = datetime.datetime.now()

    #유저가 요청한 시간대 추출
    target = reqTime.hour

    x,y,dbResult = avgVisualization(target) #배포용
    #x,y,dbResult = avgVisualization(12) #테스트용
    makeGraph(x,y,"avg")


    #이상치 제거
    if(dbResult == None):
        text = "현재 분석이 불가능하니 잠시만 기다려주세요!"
        data = {"version": "2.0","template":{"outputs":[{"simpleText":{"text":text}}]}}
    else:
        title = "이 시간대에는 평균 {0}명이 있습니다.".format(dbResult)
        description = "위 그래프는 현재 기준 전,후 3시간 \n동안의 평균 혼잡도 분석 결과입니다.\n"
        url = "http://110.34.109.166:4967/getGraph/avg/{0}".format(random.randint(1,1000))
        data = {"version": "2.0","template": {"outputs":[{"basicCard":{"title":title,"description":description,"thumbnail":{"imageUrl":url,"fixedRatio":"true","width":"640","height":"480"}}}]}}

    #응답 전송
    resp = makeResponse(data)
    return resp

### 한산한 시간대 분석값 응답 ###
@app.route("/get/quietTime",methods=['GET','POST'])
def quietT():

    kakaoReq = request.json

    #요청한 유저 정보 추출
    userId = kakaoReq["userRequest"]["user"]["id"] #배포용
    #userId = "test getQuietTime" #테스트용
    reqTime = datetime.datetime.now()

    #DB에 유저 정보 삽입
    conn.commit()
    sql = """INSERT INTO customerKakao (id, requestTime) VALUES (%s,%s)"""
    c.execute(sql,(userId,reqTime))
    conn.commit()

    x,y,dbResult = quietVisualization()
    makeGraph(x,y,"qtt")



    #이상치 제거
    if(dbResult == None):
        text = "현재 분석이 불가능하니 잠시만 기다려주세요!"
        data = {"version": "2.0","template":{"outputs":[{"simpleText":{"text":text}}]}}
    else:
        title = "평균적으로 한산한 시간대는\n {0}시, {1}시, {2}시 순입니다.".format(dbResult[0],dbResult[1],dbResult[2])
        description = "위 그래프는 평균적으로 가장 한산한 \n6시간을 분석한 그래프입니다.\n"
        url = "http://110.34.109.166:4967/getGraph/qtt/{0}".format(random.randint(1,1000))
        data = {"version": "2.0","template": {"outputs":[{"basicCard":{"title":title,"description":description,"thumbnail":{"imageUrl":url,"fixedRatio":"true","width":"640","height":"480"}}}]}}

    resp = makeResponse(data)
    return resp

# fabicon 404 오류 방지
@app.route('/favicon.ico',methods=['GET','POST'])
def favicon():
    filename = "vis.png"
    return send_file(filename, mimetype="image/gif")

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0", port=4967)
