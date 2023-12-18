from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

import pandas as pd
import numpy as np
from prophet import Prophet
import pyodbc
import datetime
import warnings

warnings.filterwarnings("ignore")

## ------------------------- server_output function:SP1TEMP1 -------------------------- ##
def server_output():
    try:
        cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                              "Server=na0vm00024.apac.bosch.com;"
                              "Database=DB_MFC2DB_SQL;"
                              "Trusted_Connection=yes;")
        current_time = datetime.datetime.now()
        past_time = current_time - datetime.timedelta(seconds=5)
        current_time = current_time.strftime("%Y-%m-%dT%H:%M:%S")
        past_time = past_time.strftime("%Y-%m-%dT%H:%M:%S")
        sql = f"SELECT TOP 1 [SP1TEMP], [TimeStamp] FROM [ChironDZ9_1] WHERE [TimeStamp] BETWEEN '{past_time}' AND '{current_time}' ORDER BY [TimeStamp] DESC"
        df = pd.read_sql_query(sql, cnxn).squeeze()
        return int(df["SP1TEMP"])

    except pyodbc.Error as e:
        sqlstate = e.args[0]
        if sqlstate == 'IM002':
            return f"An error occurred: {str(e)}. Make sure the ODBC driver is correctly installed and configured."
        else:
            return f"An error occurred: {str(e)}"
        
## ------------------------- forecasting Temp1 -------------------------- ##
def get_prophet_predictions():
    try:
        cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                              "Server=na0vm00024.apac.bosch.com;"
                              "Database=DB_MFC2DB_SQL;"
                              "Trusted_Connection=yes;")

        sql = f"SELECT CAST([TimeStamp] AS DATE) AS date, MAX([SP1Temp1]) AS max_value FROM [ChironDZ9_1] GROUP BY CAST([TimeStamp] AS DATE) ORDER BY date ASC"
        df = pd.read_sql_query(sql, cnxn, parse_dates=True)
        df.columns = ['ds', 'y']
        df['ds'] = pd.to_datetime(df['ds'])
        train = df.iloc[:len(df)-12]
        m = Prophet()
        m.fit(train)
        future = m.make_future_dataframe(periods=15, freq='D')
        forecast = m.predict(future)
        predictions = forecast.iloc[-1:][['ds','yhat', 'yhat_lower', 'yhat_upper']]
        return predictions

    except pyodbc.Error as e:
        sqlstate = e.args[0]
        if sqlstate == 'IM002':
            return f"An error occurred: {str(e)}. Make sure the ODBC driver is correctly installed and configured."
        else:
            return f"An error occurred: {str(e)}"
        
## ------------------------------------------------------------------------------------------------------##


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/fetch_data', methods=['POST'])
def fetch_data():
    server_value = server_output()
    result = get_prophet_predictions()

    yhat, yhat_lower, yhat_upper = round(result['yhat'].values[0],2), round(result['yhat_lower'].values[0],2), round(result['yhat_upper'].values[0],2)

    output = {
        'actual_temperature': server_value,
        'forecasted_temperature': yhat,
        'forecasted_min_temperature': yhat_lower,
        'forecasted_max_temperature': yhat_upper
        }

    return jsonify(output)


if __name__ == '__main__':
    app.run(host="0.0.0.0")


