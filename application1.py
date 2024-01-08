import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime,timedelta
import time
import pyttsx3 
import csv
from gtts import gTTS
import os
import webbrowser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

engine = pyttsx3.init()
train_no = '17488'
url1 = 'https://www.irctc.co.in/online-charts/api/trainComposition'
url2 = 'https://www.irctc.co.in/eticketing/protected/mapps1/trnscheduleenquiry/'+str(train_no)
url3 = 'https://www.railmitra.com/train-schedule/ndls-vskp-ap-exp-'+str(train_no)





def send_email_alert(email_content):
    receiver_email = 'prathipatijithendra@gmail.com'  # Replace with your email
    sender_email = 'jithendraprathipati4skja@gmail.com'  # Replace with receiver's email
    password = ""  # Replace with your email password

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = 'Chart Prepared Alert'

    message.attach(MIMEText(email_content, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, password)
    server.send_message(message)
    server.quit()


df_time_table = pd.DataFrame()
def get_stations_list(train_no):
    url3 = 'https://www.railmitra.com/train-schedule/ndls-vskp-ap-exp-'+train_no
    session = requests.Session()
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.railmitra.com',
    }
    session.headers.update(headers)
    response = session.get(url3, headers=headers)
    #response = requests.get(url3, headers=headers)
    if response.status_code == 200:
        # Process the response data
        data = response.text
        soup = BeautifulSoup(data, 'html.parser')
        data = soup.prettify()
        with open('train_time_table.html','w') as f:
            f.write(data)
        soup = BeautifulSoup(data, 'html.parser')
        table_rows = soup.find('table',class_ = 'table-striped').find('tbody').find_all('tr')
        running_days_spans = soup.find_all('span',class_="badge bg-secondary bg-success") #<span class="badge bg-secondary bg-success">
        running_days = []
        for r in running_days_spans:
            running_days.append(r.text.split('\n')[1].strip())
        print(running_days)
        headers = ['STATION_NAME', 'CODE', 'ARRIVAL', 'HALT', 'DEPARTURE', 'DAYS', 'DISTANCE']
        rows=[]
        for row in table_rows:
            data = [cell.get_text(strip=True) for cell in row.find_all('td')]
            rows.append(data)
        df_time_table = pd.DataFrame(rows, columns=headers)
        df_time_table.set_index('STATION_NAME', inplace=True)
        print(df_time_table)  
        station = [i for i in df_time_table.index]
        return df_time_table,station,running_days    
    else:
        print(f"Request failed with status code: {response.status_code}")
        print(response.text)
        
        
jDate = '2023-12-30'
df_time_table, station = get_stations_list(train_no)
station = [station[0]]
code = ''


def get_estimatedtime_status(train_no,jDate,station,es_time,code):
    payload = {
        "trainNo": train_no,
        "jDate": jDate,
        "boardingStation": code
    }
    chart_prepared = False
    minutes = 10
    es_time=es_time.replace('.',":")
    es_time = es_time+':00'
    chart1_time = datetime.strptime(jDate +' '+ es_time, '%Y-%m-%d %H:%M:%S')-timedelta(hours=12)
    while not chart_prepared:
        current_time = datetime.now()
        if chart1_time - timedelta(minutes=minutes)<= current_time <= chart1_time + timedelta(minutes=minutes):
            #response1 = requests.post(url1, json=payload)
            session = requests.Session()
            response1 = session.post(url1,json=payload)
            if response1.status_code == 200:
                print(response1.text)
                data = response1.json()
                if data['cdd'] is None:
                    if data['error'] == 'No Record Found':
                        sentence = "For the train "+train_no+" Alert! Alert! Chart will be prepared soon within seconds.Be ready!"
                        #send_email_alert(sentence)
                        print(sentence)
                        engine.say(sentence)
                        #engine.runAndWait()
                        tts = gTTS(text=sentence, lang='en')
                        tts.save("audio.mp3")
                        webbrowser.open('audio.mp3')
                        os.system('start audio.mp3')
                        return sentence,pd.DataFrame().to_html()
                    else:
                        print("Chart has not been prepared.................")
                        sentence = "For the train "+train_no+" Chart will be prepared at  estimated time: of"+str(chart1_time)
                        print("Chart will be prepared at  estimated time: of",chart1_time)
                        #send_email_alert(sentence)
                        time.sleep(10)
                        
                        #return "Chart will be prepared at estimated time: "+chart1_time , pd.DataFrame(index=False).to_html()
                else:
                    print("Chart prepared....................")
                    chart1_datetime = data['chartOneDate']
                    sentence = "For the train "+train_no+" The chart for your train was prepared at"+chart1_datetime  # Replace with your desired sentence
                    #send_email_alert(sentence)
                    engine.say(sentence)
                    #engine.runAndWait()
                    tts = gTTS(text=sentence, lang='en')
                    tts.save("audio.mp3")
                    webbrowser.open('audio.mp3')
                    os.system('start audio.mp3')
                    chart2_datetime = 'null'  # data['charTwoDate']
                    chart_code = data['remote']
                    chart_info = [chart_code, chart1_datetime, chart2_datetime]
                    print(chart_info)
                    rows = []
                    for c in data['cdd']:
                        rows.append([c['coachName'], c['classCode'], c['vacantBerths']])
                    col = ['coachName', 'classCode', 'vacantBerths']
                    df_response = pd.DataFrame(rows, columns=col)
                    print(df_response)
                    chart_prepared = True
                    with open("chart_time.csv", 'a', newline='') as f:
                        writer = csv.writer(f)
                        if f.tell() == 0:
                            header = ['Train_No', 'Station', 'Code', 'Chart_Code', 'Date', 'Time']
                            writer.writerow(header)
                        s = [train_no,station,code,datetime.strptime(chart1_datetime, '%Y-%m-%d %H:%M:%S').date(), datetime.strptime(chart1_datetime, '%Y-%m-%d %H:%M:%S').time()]
                        writer.writerow(s)
                    return sentence +'\n The chart vacancy is:\n' , df_response.to_html(index=False)
            else:
                print(f"Request failed with status code: {response1.status_code}")
                print(response1.text)
            #time.sleep(15)

        elif  current_time > chart1_time + timedelta(minutes=minutes):
            #response1 = requests.post(url1, json=payload)
            session = requests.Session()
            response1 = session.post(url1,json=payload)
            print(response1.text)
            if response1.status_code == 200:
                data = response1.json()
                if data['cdd'] is None:
                    if data['error'] == 'No Record Found':
                        sentence = "For the train "+train_no+" Alert! Alert! Chart will be prepared soon within seconds.Be ready!"
                        #send_email_alert(sentence)
                        print(sentence)
                        engine.say(sentence)
                        #engine.runAndWait()
                        tts = gTTS(text=sentence, lang='en')
                        tts.save("audio.mp3")
                        webbrowser.open('audio.mp3')
                        os.system('start audio.mp3')
                        return sentence,pd.DataFrame().to_html()
                    print("Chart Not Prepared.................")
                    print(data)
                    time.sleep(10)
                    #return "Chart has not been prepared yet.......",pd.DataFrame().to_html()
                else:
                    print("Chart has already prepared....................")
                    chart1_datetime = data['chartOneDate']
                    sentence = "For the train "+train_no+" The chart for your train was prepared at "+chart1_datetime  # Replace with your desired sentence
                    #send_email_alert(sentence)
                    engine.say(sentence)
                    tts = gTTS(text=sentence, lang='en')
                    tts.save("audio.mp3")
                    #engine.runAndWait()
                    webbrowser.open('audio.mp3')
                    os.system('start audio.mp3')
                    chart2_datetime = 'null'  # data['charTwoDate']
                    chart_code = data['remote']
                    chart_info = [chart_code, chart1_datetime, chart2_datetime]
                    print(chart_info)
                    rows = []
                    for c in data['cdd']:
                        rows.append([c['coachName'], c['classCode'], c['vacantBerths']])
                    col = ['coachName', 'classCode', 'vacantBerths']
                    df_response = pd.DataFrame(rows, columns=col)
                    print(df_response)
                    chart_prepared = True
                    with open("chart_time.csv", 'a', newline='') as f:
                        writer = csv.writer(f)
                        if f.tell() == 0:
                            header = ['Train_No', 'Station', 'Code', 'Chart_Code', 'Date', 'Time']
                            writer.writerow(header)
                        s = [train_no,station,code,chart_code,datetime.strptime(chart1_datetime, '%Y-%m-%d %H:%M:%S').date(), datetime.strptime(chart1_datetime, '%Y-%m-%d %H:%M:%S').time()]
                        writer.writerow(s)
                    print(sentence+"\n The chart vacancy is: \n"+df_response.to_string())
                    return sentence+"\n The chart vacancy is: \n",df_response.to_html(index=False)
            else:
                print(f"Request failed with status code: {response1.status_code}")
                print(response1.text)

        elif  chart1_time - timedelta(minutes=minutes) > current_time:
            print("Chart will be prepared at estimated time: ",chart1_time)
            #sentence = "For  the train "+train_no+" Chart will be prepared at estimated time: "+ str(chart1_time)
            send_email_alert(sentence)
            tts = gTTS(text=sentence, lang='en')
            tts.save("audio.mp3")
        

def get_prev_status(train_no,jDate,station):
    code = ''
    sentence = "Hello"
    df_time_table, station_list = get_stations_list(train_no) 
    if (datetime.strptime(jDate + ' 00:00:10', '%Y-%m-%d %H:%M:%S').date() < datetime.now().date()):
        print("Choose journey date properly.........")
        return "Choose journey date properly"
    chart1_datetime = 0
    chart_code = 0
    code = df_time_table.loc[station, 'CODE']
    dept_time = df_time_table.loc[station, 'DEPARTURE']
    dept_time = dept_time.replace('.', ':')
    dept_time = dept_time + ":0"
    day = df_time_table.loc[station, 'DAYS']
    prev_datetime = datetime.strptime(jDate + ' 00:00:10', '%Y-%m-%d %H:%M:%S') - timedelta(days=1)
    prev_date = prev_datetime.strftime("%Y-%m-%d")
    print('prev_datetime',prev_datetime)
    prev_payload = {
        "trainNo": train_no,
        "jDate": prev_date,
        "boardingStation": code
    }
    
    response1 = requests.post(url1, json=prev_payload)
    df_prev_response = pd.DataFrame()

    if response1.status_code == 200:
        print(response1.text)
        data = response1.json()
        if data['cdd'] is None:
            print("Chart has not been prepared.................")
            return get_estimatedtime_status(train_no,jDate,station,df_time_table.loc[station,'DEPARTURE'],df_time_table.loc[station,'CODE'])
            #return "Chart has not been prepared..........",pd.DataFrame().to_html()
        else:
            print("Chart prepared....................")
            chart1_datetime = data['chartOneDate']
            chart2_datetime = 'null'  # data['charTwoDate']
            chart_code = data['remote']
            chart_info = [chart_code, chart1_datetime, chart2_datetime]
            print(chart_info)
            rows = []
            for c in data['cdd']:
                rows.append([c['coachName'], c['classCode'], c['vacantBerths']])
            col = ['coachName', 'classCode', 'vacantBerths']
            df_prev_response = pd.DataFrame(rows, columns=col)
            print(df_prev_response)
            chart1_time = datetime.strptime(chart1_datetime, "%Y-%m-%d %H:%M:%S") + timedelta(days = 1)
            sentence = "Chart will be prepared at estimated time: "+ str(chart1_time)+'.'
            #send_email_alert(sentence)
    return sentence+'You will be informed when it is ready.',pd.DataFrame().to_html()





 


def get_status(train_no,jDate,station):
    code = ''
    df_time_table, station_list,running_days = get_stations_list(train_no)
    jDatetime  = datetime.strptime(jDate + ' 00:00:10', '%Y-%m-%d %H:%M:%S')
    week_day = jDatetime.strftime('%a')
    day = int(df_time_table['DAYS'])
    ind = running_days.indexof(week_day)
    ind = (ind+day-1)%7
    if (datetime.strptime(jDate + ' 00:00:10', '%Y-%m-%d %H:%M:%S').date() < datetime.now().date()):
        print("Choose journey date properly.........")
        return "Choose journey date properly"
    chart1_datetime = 0
    chart_code = 0
    code = df_time_table.loc[station, 'CODE']
    dept_time = df_time_table.loc[station, 'DEPARTURE']
    dept_time = dept_time.replace('.', ':')
    dept_time = dept_time + ":0"
    day = df_time_table.loc[station, 'DAYS']
    prev_datetime = datetime.strptime(jDate + ' 00:00:10', '%Y-%m-%d %H:%M:%S') - timedelta(days=1)
    prev_date = prev_datetime.strftime("%Y-%m-%d")
    print('prev_datetime',prev_datetime)
    prev_payload = {
        "trainNo": train_no,
        "jDate": prev_date,
        "boardingStation": code
    }
    
    response1 = requests.post(url1, json=prev_payload)
    df_prev_response = pd.DataFrame()

    if response1.status_code == 200:
        print(response1.text)
        data = response1.json()
        if data['cdd'] is None:
            print("Chart has not been prepared.................")
            return "Chart has not been prepared.........."
        else:
            print("Chart prepared....................")
            chart1_datetime = data['chartOneDate']
            chart2_datetime = 'null'  # data['charTwoDate']
            chart_code = data['remote']
            chart_info = [chart_code, chart1_datetime, chart2_datetime]
            print(chart_info)
            rows = []
            for c in data['cdd']:
                rows.append([c['coachName'], c['classCode'], c['vacantBerths']])
            col = ['coachName', 'classCode', 'vacantBerths']
            df_prev_response = pd.DataFrame(rows, columns=col)
            print(df_prev_response)
    
    chart1_time = datetime.strptime(chart1_datetime, "%Y-%m-%d %H:%M:%S") + timedelta(days = 1)
    payload = {
        "trainNo": train_no,
        "jDate": jDate,
        "boardingStation": code
    }

    chart_prepared = False
    sentence = ""

    minutes = 50
    while not chart_prepared:    
        current_time = datetime.now()
        #minutes = minutes+1

        if chart1_time - timedelta(minutes=minutes)<= current_time <= chart1_time + timedelta(minutes=minutes):
            #response1 = requests.post(url1, json=payload)
            session = requests.Session()
            response1 = session.post(url1,json=payload)
            if response1.status_code == 200:
                print(response1.text)
                data = response1.json()
                if data['cdd'] is None:
                    if data['error'] == 'No Record Found':
                        sentence = "For the train "+train_no+" Alert! Alert! Chart will be prepared soon within seconds.Be ready!"
                        #send_email_alert(sentence)
                        print(sentence)
                        engine.say(sentence)
                        #engine.runAndWait()
                        tts = gTTS(text=sentence, lang='en')
                        tts.save("audio.mp3")
                        webbrowser.open('audio.mp3')
                        os.system('start audio.mp3')
                        return sentence,pd.DataFrame().to_html()
                    else:
                        print("Chart has not been prepared.................")
                        print("Chart will be prepared at  estimated time: of",chart1_time)
                        time.sleep(10)
                        
                        #return "Chart will be prepared at estimated time: "+chart1_time , pd.DataFrame(index=False).to_html()
                else:
                    print("Chart prepared....................")
                    chart1_datetime = data['chartOneDate']
                    sentence ="For the train  "+train_no+ " The chart for your train was prepared at"+chart1_datetime  # Replace with your desired sentence
                    #send_email_alert(sentence)
                    engine.say(sentence)
                    #engine.runAndWait()
                    tts = gTTS(text=sentence, lang='en')
                    tts.save("./templates/audio.mp3")
                    webbrowser.open('./templates/audio.mp3')
                    os.system('start ./templates/audio.mp3')
                    chart2_datetime = 'null'  # data['charTwoDate']
                    chart_code = data['remote']
                    chart_info = [chart_code, chart1_datetime, chart2_datetime]
                    print(chart_info)
                    rows = []
                    for c in data['cdd']:
                        rows.append([c['coachName'], c['classCode'], c['vacantBerths']])
                    col = ['coachName', 'classCode', 'vacantBerths']
                    df_response = pd.DataFrame(rows, columns=col)
                    print(df_response)
                    chart_prepared = True
                    with open("chart_time.csv", 'a', newline='') as f:
                        writer = csv.writer(f)
                        if f.tell() == 0:
                            header = ['Train_No', 'Station', 'Code', 'Chart_Code', 'Date', 'Time']
                            writer.writerow(header)
                        s = [train_no,station,code,chart_code,datetime.strptime(chart1_datetime, '%Y-%m-%d %H:%M:%S').date(), datetime.strptime(chart1_datetime, '%Y-%m-%d %H:%M:%S').time()]
                        writer.writerow(s)
                    return sentence +'\n The chart vacancy is:\n' , df_response.to_html(index=False)
            else:
                print(f"Request failed with status code: {response1.status_code}")
                print(response1.text)
            #time.sleep(15)

        elif  current_time > chart1_time + timedelta(minutes=minutes):
            #response1 = requests.post(url1, json=payload)
            session = requests.Session()
            response1 = session.post(url1,json=payload)
            print(response1.text)
            if response1.status_code == 200:
                data = response1.json()
                if data['cdd'] is None:
                    if data['error'] == 'No Record Found':
                        sentence = "For the train "+train_no+" Alert! Alert! Chart will be prepared soon within seconds.Be ready!"
                        #send_email_alert(sentence)
                        print(sentence)
                        engine.say(sentence)
                        #engine.runAndWait()
                        tts = gTTS(text=sentence, lang='en')
                        tts.save("./templates/audio.mp3")
                        webbrowser.open('./templates/audio.mp3')
                        os.system('start ./templates/audio.mp3')
                        return sentence,pd.DataFrame().to_html()
                    print("Chart Not Prepared.................")
                    print(data)
                    #return "Chart has not been prepared yet.......",pd.DataFrame().to_html()
                else:
                    print("Chart has already prepared....................")
                    chart1_datetime = data['chartOneDate']
                    sentence = "For the train "+train_no+" The chart for your train was prepared at "+chart1_datetime  # Replace with your desired sentence
                    #send_email_alert(sentence)
                    engine.say(sentence)
                    tts = gTTS(text=sentence, lang='en')
                    tts.save(r"./templates/audio.mp3")
                    #engine.runAndWait()
                    webbrowser.open('./templates/audio.mp3')
                    os.system('start ./templates/audio.mp3')
                    chart2_datetime = 'null'  # data['charTwoDate']
                    chart_code = data['remote']
                    chart_info = [chart_code, chart1_datetime, chart2_datetime]
                    print(chart_info)
                    rows = []
                    for c in data['cdd']:
                        rows.append([c['coachName'], c['classCode'], c['vacantBerths']])
                    col = ['coachName', 'classCode', 'vacantBerths']
                    df_response = pd.DataFrame(rows, columns=col)
                    print(df_response)
                    with open("chart_time.csv", 'a', newline='') as f:
                        writer = csv.writer(f)
                        if f.tell() == 0:
                            header = ['Train_No', 'Station', 'Code', 'Chart_Code', 'Date', 'Time']
                            writer.writerow(header)
                        s = [train_no,station,code,chart_code,datetime.strptime(chart1_datetime, '%Y-%m-%d %H:%M:%S').date(), datetime.strptime(chart1_datetime, '%Y-%m-%d %H:%M:%S').time()]
                        writer.writerow(s)
                    chart_prepared = True
                    print(sentence+"\n The chart vacancy is: \n"+df_response.to_string())
                    return sentence+"\n The chart vacancy is: \n",df_response.to_html(index=False)
            else:
                print(f"Request failed with status code: {response1.status_code}")
                print(response1.text)

        elif  chart1_time - timedelta(minutes=minutes) > current_time:
            print("Chart will be prepared at estimated time: ",chart1_time)
            sentence = "For the train "+train_no+" Chart will be prepared at estimated time: "+ str(chart1_time)
            #send_email_alert(sentence)
            tts = gTTS(text=sentence, lang='en')
            tts.save(r"./templates/audio.mp3")
        time.sleep(10)
            
            
            