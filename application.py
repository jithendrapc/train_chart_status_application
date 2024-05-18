import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import csv
from gtts import gTTS

train_no = '17488'
url1 = 'https://www.irctc.co.in/online-charts/api/trainComposition'
url3 = 'https://www.railmitra.com/train-schedule/ndls-vskp-ap-exp-' + train_no
url4 = 'https://www.irctc.co.in/online-charts/api/vacantBerth'


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
    if response.status_code == 200:
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
        return None, None, None
        
prev_chart_status = ''
chart1_datetime = ''
chart_code = ''
code = ''



def get_prev_status(train_no,jDate,station):
    sentence = "Hello, "
    df_time_table, station_list,running_days = get_stations_list(train_no) 
    global code
    global prev_chart_status
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
            prev_chart_status = False
            print("Chart has not been prepared.................")
            sentence ="For the train "+ str(train_no) +", estimated time cannot be calculated."
            return sentence+' You will be informed when it is ready.', pd.DataFrame().to_html(), [None]*4
        else:
            print("Chart prepared....................")
            prev_chart_status = True
            global chart1_datetime
            chart1_datetime = data['chartOneDate']
            chart2_datetime = 'null'  # data['charTwoDate']
            global chart_code
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
            sentence = "For the train number: "+ str(train_no)+ ", chart will be prepared at estimated time, "+ str(chart1_time)+'.'
            tts = gTTS(text=sentence+' You will be informed when it is ready.', lang='en')
            tts.save("static/audio.mp3")
            return sentence, pd.DataFrame().to_html(), [chart1_datetime, True, chart_code, code]
    return sentence+' You will be informed when it is ready.',pd.DataFrame().to_html(),[chart1_datetime,prev_chart_status,chart_code,code]


def get_status(train_no,jDate,station,dstation):
    _,_,list_details = get_prev_status(train_no,jDate,station)
    chart1_datetime = list_details[0]
    prev_chart_status = list_details[1]
    chart_code = list_details[2]
    code = list_details[3]
    df_time_table, station_list,running_days = get_stations_list(train_no)
    jDatetime  = datetime.strptime(jDate + ' 00:00:10', '%Y-%m-%d %H:%M:%S')
    week_day = jDatetime.strftime('%a')
    day = int(df_time_table.loc[station,'DAYS'])
    total_days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
    run_days=[]
    for dayz in running_days:
        ind = total_days.index(dayz)
        ind = (ind+day-1)%7
        run_days.append(total_days[ind])
    if week_day not in run_days:
        print("Choose journey date and train properly.........")
        return "Choose journey date and train properly", pd.DataFrame().to_html(), pd.DataFrame().to_html(), pd.DataFrame().to_html()
    
    if not prev_chart_status:
        es_time = df_time_table.loc[station,'DEPARTURE']
        es_time=es_time.replace('.',":")
        es_time = es_time+':00'
        print(jDate +' '+ es_time)
        chart1_time = datetime.strptime(jDate +' '+ es_time, '%Y-%m-%d %H:%M:%S')-timedelta(hours=12)
    else:
        chart1_time = datetime.strptime(chart1_datetime, "%Y-%m-%d %H:%M:%S") + timedelta(days = 1)
        
        
    code = df_time_table.loc[station, 'CODE']
    dcode = df_time_table.loc[dstation, 'CODE']
    dept_time = df_time_table.loc[station, 'DEPARTURE']
    dept_time = dept_time.replace('.', ':')
    dept_time = dept_time + ":0"
    day = df_time_table.loc[station, 'DAYS']
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
                        sentence = "Alert! Alert! For the train "+train_no+", Chart will be prepared soon (within seconds). Be ready!"
                        print(sentence)
                        tts = gTTS(text=sentence, lang='en')
                        tts.save("static/audio.mp3")
                        return sentence,pd.DataFrame().to_html(),pd.DataFrame().to_html(),pd.DataFrame().to_html()
                    else:
                        print("Chart has not been prepared.................")
                        print("Chart will be prepared at  estimated time: of",chart1_time)
                        time.sleep(10)
                        
                        #return "Chart will be prepared at estimated time: "+chart1_time , pd.DataFrame(index=False).to_html()
                else:
                    print("Chart prepared....................")
                    chart1_datetime = data['chartOneDate']
                    sentence ="For the train  "+train_no+ ", the chart for your train was prepared at "+chart1_datetime  # Replace with your desired sentence
                    tts = gTTS(text=sentence, lang='en')
                    tts.save("static/audio.mp3")
                    chart2_datetime = 'null'  # data['charTwoDate']
                    chart_code = data['remote']
                    chart_info = [chart_code, chart1_datetime, chart2_datetime]
                    classes = set()
                    print(chart_info)
                    rows = []
                    for c in data['cdd']:
                        rows.append([c['coachName'], c['classCode'], c['vacantBerths']])
                        classes.add(c['classCode'])
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
                        
                    df = pd.DataFrame()
                    for classCode in classes:
                        payload2 = {
                            "trainNo": train_no,
                            "jDate": jDate,
                            "boardingStation": code,
                            "chartType" : 1,
                            "cls" : classCode,
                            "remoteStation" : data['remote'],
                            "trainSourceStation" : data['from']    
                        }
                        response2 = session.post(url4,json=payload2).json()   
                        df_class = pd.DataFrame(response2['vbd'])
                        df = pd.concat([df, df_class], ignore_index=True)
                    df = df.sort_values(by=['coachName', 'berthNumber'])
                    s_d_vdf = df[df['from'] == code] 
                    s_d_vdf = s_d_vdf[s_d_vdf['to'] == dcode]                  
                        
                    
                    return sentence +'\n The chart vacancy is:\n' , df_response.to_html(index=False),df.to_html(index=False),s_d_vdf.to_html(index=False)
            else:
                print(f"Request failed with status code: {response1.status_code}")
                print(response1.text)
            

        elif  current_time > chart1_time + timedelta(minutes=minutes):
            session = requests.Session()
            response1 = session.post(url1,json=payload)
            print(response1.text)
            if response1.status_code == 200:
                data = response1.json()
                if data['cdd'] is None:
                    if data['error'] == 'No Record Found':
                        sentence = "For the train "+train_no+", Alert! Alert! Chart will be prepared soon(within seconds).Be ready!"
                        print(sentence)
                        tts = gTTS(text=sentence, lang='en')
                        tts.save("static/audio.mp3")
                        return sentence,pd.DataFrame().to_html()
                    print("Chart Not Prepared.................")
                    print(data)
                    #return "Chart has not been prepared yet.......",pd.DataFrame().to_html()
                else:
                    print("Chart has already prepared....................")
                    chart1_datetime = data['chartOneDate']
                    sentence = "For the train "+train_no+", the chart for your train was prepared at "+chart1_datetime  # Replace with your desired sentence
                    tts = gTTS(text=sentence, lang='en')
                    tts.save(r"static/audio.mp3")
                    chart2_datetime = 'null'  # data['charTwoDate']
                    chart_code = data['remote']
                    chart_info = [chart_code, chart1_datetime, chart2_datetime]
                    print(chart_info)
                    rows = []
                    classes = set()
                    for c in data['cdd']:
                        rows.append([c['coachName'], c['classCode'], c['vacantBerths']])
                        classes.add(c['classCode'])
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
                        
                
                    df = pd.DataFrame()
                    for classCode in classes:
                        payload2 = {
                            "trainNo": train_no,
                            "jDate": jDate,
                            "boardingStation": code,
                            "chartType" : 1,
                            "cls" : classCode,
                            "remoteStation" : data['remote'],
                            "trainSourceStation" : data['from']    
                        }
                        response2 = session.post(url4,json=payload2).json()   
                        df_class = pd.DataFrame(response2['vbd'])
                        df = pd.concat([df, df_class], ignore_index=True)
                    df = df.sort_values(by=['coachName', 'berthNumber'])
                    s_d_vdf = df[df['from'] == code] 
                    s_d_vdf = s_d_vdf[s_d_vdf['to'] == dcode]
                    df.to_excel(r'static\total_vacant_berths.xlsx', index=False)
                    s_d_vdf.to_excel(r'static\boarding_destination_vacant_berths.xlsx', index=False)
                        
                        
                    chart_prepared = True
                    print(sentence+"\n The chart vacancy is: \n"+df_response.to_string())
                    return sentence+"\n The chart vacancy is: \n",df_response.to_html(index=False),df.to_html(index=False),s_d_vdf.to_html(index=False)
            else:
                print(f"Request failed with status code: {response1.status_code}")
                print(response1.text)

        elif  chart1_time - timedelta(minutes=minutes) > current_time:
            print("Chart will be prepared at estimated time: ",chart1_time)
            sentence = "For the train "+train_no+", the chart will be prepared at estimated time "+ str(chart1_time)
            tts = gTTS(text=sentence, lang='en')
            tts.save(r"static/audio.mp3")
        time.sleep(10)