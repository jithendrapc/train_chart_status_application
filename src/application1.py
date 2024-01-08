import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime,timedelta
import time
import pyttsx3 
import csv

engine = pyttsx3.init()
train_no = 17488
url1 = 'https://www.irctc.co.in/online-charts/api/trainComposition'
url2 = 'https://www.irctc.co.in/eticketing/protected/mapps1/trnscheduleenquiry/'+str(train_no)
url3 = 'https://www.railmitra.com/train-schedule/ndls-vskp-ap-exp-'+str(train_no)


df_time_table = pd.DataFrame()
def get_stations_list(train_no):
    url3 = 'https://www.railmitra.com/train-schedule/ndls-vskp-ap-exp-'+str(train_no)
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
        headers = ['STATION_NAME', 'CODE', 'ARRIVAL', 'HALT', 'DEPARTURE', 'DAYS', 'DISTANCE']
        rows=[]
        for row in table_rows:
            data = [cell.get_text(strip=True) for cell in row.find_all('td')]
            rows.append(data)
        df_time_table = pd.DataFrame(rows, columns=headers)
        df_time_table.set_index('STATION_NAME', inplace=True)
        print(df_time_table)  
        station = [i for i in df_time_table.index]
        return df_time_table,station    
    else:
        print(f"Request failed with status code: {response.status_code}")
        print(response.text)
        
        
jDate = '2023-12-30'
df_time_table, station = get_stations_list(train_no)
station = [station[0]]
code = 0


for i in station:
    if (datetime.strptime(jDate + ' 00:00:10', '%Y-%m-%d %H:%M:%S').date() < datetime.now().date()):
        print("Choose journey date properly.........")
        break
    chart1_datetime = 0
    chart_code = 0
    code = df_time_table.loc[i, 'CODE']
    dept_time = df_time_table.loc[i, 'DEPARTURE']
    dept_time = dept_time.replace('.', ':')
    dept_time = dept_time + ":0"
    day = df_time_table.loc[i, 'DAYS']
    prev_datetime = datetime.strptime(jDate + ' 00:00:10', '%Y-%m-%d %H:%M:%S') - timedelta(days=1)
    prev_date = prev_datetime.strftime("%Y-%m-%d")
    print('prev_datetime',prev_datetime)
    prev_payload = {
        "trainNo": str(train_no),
        "jDate": prev_date,
        "boardingStation": code
    }
    
    response1 = requests.post(url1, json=prev_payload)
    df_prev_response = pd.DataFrame()

    if response1.status_code == 200:
        data = response1.json()
        if data['cdd'] is None:
            print("Chart has not been prepared.................")
            print(data)
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
        "trainNo": str(train_no),
        "jDate": jDate,
        "boardingStation": code
    }

    chart_prepared = False

    while not chart_prepared:
        current_time = datetime.now()

        if chart1_time - timedelta(minutes=5)<= current_time <= chart1_time + timedelta(minutes=5):
            response1 = requests.post(url1, json=payload)
            if response1.status_code == 200:
                data = response1.json()
                if data['cdd'] is None:
                    if data['error'] == 'No Record Found':
                        sentence = "Chart will be prepared soon within seconds.Be ready!"
                        print(sentence)
                        engine.say(sentence)
                        #engine.runAndWait()
                    else:
                        print("Chart has not been prepared.................")
                        print("Chart will be prepared at estimated time: ",chart1_time)
                else:
                    print("Chart prepared....................")
                    chart1_datetime = data['chartOneDate']
                    sentence = "The chart for your train was prepared at"+chart1_datetime  # Replace with your desired sentence
                    engine.say(sentence)
                    engine.runAndWait()
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
                        s = [train_no,i,code,datetime.strptime(chart1_datetime, '%Y-%m-%d %H:%M:%S').date(), datetime.strptime(chart1_datetime, '%Y-%m-%d %H:%M:%S').time()]
                        writer.writerow(s)
            else:
                print(f"Request failed with status code: {response1.status_code}")
                print(response1.text)
            time.sleep(15)

        elif  current_time > chart1_time + timedelta(minutes=1):
            response1 = requests.post(url1, json=payload)
            if response1.status_code == 200:
                data = response1.json()
                if data['cdd'] is None:
                    print("Chart Not Prepared.................")
                    print(data)
                else:
                    print("Chart has already prepared....................")
                    chart1_datetime = data['chartOneDate']
                    sentence = "The chart for your train was prepared at"+chart1_datetime  # Replace with your desired sentence
                    engine.say(sentence)
                    #engine.runAndWait()
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
            else:
                print(f"Request failed with status code: {response1.status_code}")
                print(response1.text)

        elif  chart1_time - timedelta(minutes=1) > current_time:
            print("Chart will be prepared at estimated time: ",chart1_time)
           
            
            
