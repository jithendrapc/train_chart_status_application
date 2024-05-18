from flask import Flask, render_template, request, jsonify
from application import get_stations_list,get_status,get_prev_status
import pandas as pd
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.application import MIMEApplication
from email.encoders import encode_base64

app = Flask(__name__)

from_email_address = 'testmail.andhra@gmail.com'
from_email_pass = "ngyf svbh uwtp swic"

server = None
def initialize_server():
    global server
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email_address, from_email_pass)

def is_connection_live(server):
    try:
        server.noop()
        return True
    except (smtplib.SMTPServerDisconnected, smtplib.SMTPException):
        return False
    
def send_email(to_email, subject, status, table, ftable, sdtable, audio_file_path, total_excel_file_path, total_sd_excel_file_path ):
    if is_connection_live(server):
        msg = MIMEMultipart()
        msg['From'] = from_email_address
        msg['To'] = to_email
        msg['Subject'] = subject

        body = f"""\
        <html>
        <body>
            <p> Dear Passenger, </p>
            <br>
            <p>{status}</p>
            <h4> Vacancy chart between boarding and destination stations only: </h4>
            {sdtable}
            <h4> Vacancy chart between all stations: </h4>
            {ftable}
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        with open(audio_file_path, 'rb') as f:
            audio_data = MIMEAudio(f.read(), 'mp3')
            audio_data.add_header('Content-Disposition', 'attachment', filename='audio.mp3')
            encode_base64(audio_data)
            msg.attach(audio_data)

        if (total_excel_file_path != 'NA'):
            with open(total_excel_file_path, 'rb') as f:
                excel_data = MIMEApplication(f.read(), 'xlsx')
                excel_data.add_header('Content-Disposition', 'attachment', filename='total vacant berths.xlsx')
                encode_base64(excel_data)
                msg.attach(excel_data)

            with open(total_sd_excel_file_path, 'rb') as f:
                excel_data1 = MIMEApplication(f.read(), 'xlsx')
                excel_data1.add_header('Content-Disposition', 'attachment', filename='vacant berths between boarding and destination stations.xlsx')
                encode_base64(excel_data1)
                msg.attach(excel_data1)

        server.sendmail(from_email_address, to_email, msg.as_string())
    else:
        initialize_server()
        send_email(to_email, subject, status, table, ftable, sdtable, audio_file_path, total_excel_file_path, total_sd_excel_file_path)

    
    
@app.route("/")
def index():
    return render_template('index.html')

@app.route('/stations/<train_no>')
def get_stations(train_no):
    df_time_table, stations, running_days = get_stations_list(train_no)
    return jsonify({'stations': stations})

@app.route('/prev-chart-status', methods=['POST'])
def prev_chart_status():
    train_no = request.json['train_number']
    jDate = request.json['journey_date']
    station = request.json['station']
    email = request.json['email']

    status, table, list_details = get_prev_status(train_no, jDate, station)
    chart_status = {'status': status, 'table': table}

    send_email(email, 'Estimated Chart Status', status, table,table,table, r'static\audio.mp3','NA','NA')
    return jsonify(chart_status)

@app.route('/chart-status', methods=['POST'])
def check_chart_status():
    train_no = request.json['train_number']
    jDate = request.json['journey_date']
    station = request.json['station']
    dstation = request.json['dstation']
    email = request.json['email']

    status, table, ftable, sdtable = get_status(train_no, jDate, station, dstation)
    chart_status = {'status': status, 'table': table, 'ftable': ftable, 'sdtable': sdtable}

    send_email(email, 'Live Chart Status', status, table, ftable, sdtable, r'static\audio.mp3', r'static\total_vacant_berths.xlsx', r'static\boarding_destination_vacant_berths.xlsx')
    return jsonify(chart_status)


    

        
        
if __name__ == '__main__':
    initialize_server()
    try:
        app.run(debug=True)
    finally:
        server.quit()
        print("SMTP Connection Closed")

 
 


 
 
 