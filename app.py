from flask import Flask, render_template, request, jsonify
import pyodbc
import matplotlib
matplotlib.use('agg')  # Set non-interactive backend
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

server = 'ekthaserver.database.windows.net'
driver='ODBC Driver 17 for SQL Server'
database='ekthadatabase'
username = 'rohitshaw'  # Add your SQL Server username
password = 'kolkata@123'  # Add your SQL Server password
 
# Function to establish database connection
def connect_db():
    connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    return pyodbc.connect(connection_string)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/get_sales_data', methods=['GET'])
def get_sales_data():
    try:
        product_id = request.args.get('product_id')
        year = request.args.get('year')

        # Query database for seasonal sales data based on product_id and year
        cnxn = connect_db()
        cursor = cnxn.cursor()
        query = f'''
            SELECT
                CASE 
                    WHEN DATEPART(month, Movement_date) IN (12, 1, 2) THEN 'Winter'
                    WHEN DATEPART(month, Movement_date) IN (3, 4, 5) THEN 'Spring'
                    WHEN DATEPART(month, Movement_date) IN (6, 7, 8) THEN 'Summer'
                    WHEN DATEPART(month, Movement_date) IN (9, 10, 11) THEN 'Autumn'
                END AS season,
                SUM(Quantity_changed) AS total_sales
            FROM Stock_Movement
            WHERE Product_id = {product_id} AND YEAR(Movement_date) = {year} AND Reason = 'Sale'
            GROUP BY
                CASE 
                    WHEN DATEPART(month, Movement_date) IN (12, 1, 2) THEN 'Winter'
                    WHEN DATEPART(month, Movement_date) IN (3, 4, 5) THEN 'Spring'
                    WHEN DATEPART(month, Movement_date) IN (6, 7, 8) THEN 'Summer'
                    WHEN DATEPART(month, Movement_date) IN (9, 10, 11) THEN 'Autumn'
                END
        '''
        cursor.execute(query)
        sales_data = cursor.fetchall()
        cursor.close()
        cnxn.close()

        # Prepare data for plotting
        seasons = ['Winter', 'Spring', 'Summer', 'Autumn']
        total_sales = [0, 0, 0, 0]  # Initialize sales for each season

        for row in sales_data:
            if row.season in seasons:
                index = seasons.index(row.season)
                total_sales[index] += -row.total_sales

        # Generate plot
        plt.figure(figsize=(10, 6))
        plt.bar(seasons, total_sales, color='blue')
        plt.xlabel('Season')
        plt.ylabel('Total Sales')
        plt.title(f'Seasonal Sales Data for Product ID {product_id} in Year {year}')

        # Save plot to a BytesIO object
        image_stream = BytesIO()
        plt.savefig(image_stream, format='png')
        image_stream.seek(0)
        plot_img = base64.b64encode(image_stream.getvalue()).decode('utf-8')
        plt.close()

        return jsonify({'plot_img': plot_img})

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
