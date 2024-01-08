from flask import Flask, render_template, request, jsonify
from application import get_stations_list,get_status,get_prev_status
import pandas as pd
app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')
# Fetch station data route
@app.route('/stations/<train_no>')
def get_stations(train_no):
    df_time_table,stations,running_days = get_stations_list(train_no) # Fetch stations from database or API
    return jsonify({'stations': stations})


@app.route('/prev-chart-status', methods=['POST'])
def prev_chart_status():
    train_no = request.json['train_number']
    jDate = request.json['journey_date']
    station = request.json['station']
    status,table,list_details = get_prev_status(train_no,jDate,station)
    chart_status = {'status':status ,'table':table}
    return jsonify(chart_status)



# Route to check chart preparation status
@app.route('/chart-status', methods=['POST'])
def check_chart_status():
    train_no = request.json['train_number']
    jDate = request.json['journey_date']
    station = request.json['station']
    status,table = get_status(train_no,jDate,station)
    chart_status = {'status':status ,'table':table}
    return jsonify(chart_status)


if __name__ == '__main__':
    app.run(debug=True)
