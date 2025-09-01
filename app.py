# app.py

import pyodbc
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request, jsonify
#from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from config import cfg
from sbcutils import PyRibbonClient
from scheduler_task import run_scheduled_updates

# --- DATABASE HELPER FUNCTIONS ---
def get_db_connection():
    """Establishes a connection to the MS SQL database."""
    print("Establishing database connection...")
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            f'SERVER={cfg.DB_SERVER};'
            f'DATABASE={cfg.DB_NAME};'
            f'TRUSTED_CONNECTION={cfg.DB_TRUSTEDCONNECTION};'
        )
        conn.autocommit = True
        return conn
    except pyodbc.Error as ex:
        print(f"Database connection error: {ex}")
        return None

def send_email_notification(user_name, mobile, scheduled_date):
    """Sends an email notification for a new schedule."""
    if not cfg.SMTP_SERVER:
        print("Email not configured. Skipping notification.")
        return

    msg = EmailMessage()
    msg.set_content(
        f"A new on-call schedule has been created:\n\n"
        f"User: {user_name}\n"
        f"Mobile: {mobile}\n"
        f"Date: {scheduled_date.strftime('%Y-%m-%d %H:%M')}\n"
    )
    msg['Subject'] = 'New On-Call Schedule Created'
    msg['From'] = cfg.FROM_PERSON
    msg['To'] = user_name + "@transalta.com"
    print("emailing", msg['To'])
    try:
        with smtplib.SMTP(cfg.SMTP_SERVER, cfg.SMTP_PORT) as s:
            s.starttls()
            s.send_message(msg)
        print("Email notification sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")


# --- FLASK APP INITIALIZATION ---
app = Flask(__name__)
app.config.from_object(cfg)
sbc_client = PyRibbonClient()

# --- WEB PAGE ROUTE ---
@app.route('/audssoncall/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

# --- API ROUTES ---
@app.route('/audssoncall/api/users', methods=['GET', 'POST'])
def manage_users():
    print("Received request for /audssoncall/api/users")
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT id, name, mobile FROM OnCallUsers ORDER BY name")
        users = [{'id': row[0], 'name': row[1], 'mobile': row[2]} for row in cursor.fetchall()]
        conn.close()
        return jsonify(users)

    if request.method == 'POST':
        data = request.get_json()
        if not data or 'name' not in data or 'mobile' not in data:
            conn.close()
            return jsonify({'error': 'Name and mobile are required'}), 400
        
        sql = "INSERT INTO OnCallUsers (name, mobile) VALUES (?, ?)"
        cursor.execute(sql, data['name'], data['mobile'])
        conn.close()
        return jsonify({'message': 'User added successfully'}), 201
    
@app.route('/audssoncall/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    if not data or 'mobile' not in data:
        return jsonify({'error': 'Mobile number is required'}), 400
        
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    sql = "UPDATE OnCallUsers SET mobile = ? WHERE id = ?"
    cursor.execute(sql, (data['mobile'], user_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
        
    conn.close()
    return jsonify({'message': 'User updated successfully'})

@app.route('/audssoncall/api/oncall', methods=['GET', 'POST'])
def manage_oncall():
    print(f"sbc_client instance: {sbc_client}")
    if request.method == 'GET':
        statuses = sbc_client.sbc_interaction(action="check")
        return jsonify(statuses)
    
    if request.method == 'POST':
        data = request.get_json()
        mobile = data.get('mobile', '').replace(" ", "")
        if not mobile:
            return jsonify({'error': 'Mobile number is required for update'}), 400
        statuses = sbc_client.sbc_interaction(mobile=mobile, action="update")
        return jsonify(statuses)

@app.route('/audssoncall/api/schedule', methods=['GET', 'POST'])
def manage_schedules():
    """API endpoint to view and create schedules."""
    conn = get_db_connection()
    if conn is None: return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    
    if request.method == 'GET':
        # ... (your GET logic is correct) ...
        sql = """
            SELECT s.id, u.name, u.mobile, s.scheduled_datetime, s.status
            FROM OnCallSchedules s
            JOIN OnCallUsers u ON s.user_id = u.id
            WHERE s.scheduled_datetime >= GETDATE() AND s.status = 'pending'
            ORDER BY s.scheduled_datetime
        """
        cursor.execute(sql)
        schedules = [
            {
                'id': row[0], 'name': row[1], 'mobile': row[2], 
                'scheduled_datetime': row[3].isoformat(), 'status': row[4]
            } for row in cursor.fetchall()
        ]
        conn.close()
        return jsonify(schedules)

    if request.method == 'POST':
        # Ensure the request body is valid JSON
        data = request.get_json()
        if data is None:
            conn.close()
            return jsonify({'error': 'Request body must be valid JSON'}), 400

        user_id = data.get('user_id')
        scheduled_datetime_str = data.get('scheduled_datetime')

        if not all([user_id, scheduled_datetime_str]):
            conn.close()
            return jsonify({'error': 'User ID and schedule datetime are required'}), 400
        
        try:
            scheduled_datetime = datetime.fromisoformat(scheduled_datetime_str)
        except ValueError:
            conn.close()
            return jsonify({'error': 'Invalid datetime format'}), 400
        
        sql = "INSERT INTO OnCallSchedules (user_id, scheduled_datetime) VALUES (?, ?)"
        cursor.execute(sql, (user_id, scheduled_datetime))
        
        cursor.execute("SELECT name, mobile FROM OnCallUsers WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        try:
            if user:
                print(f"Sending email to {user[0]} at {user[1]} for schedule on {scheduled_datetime}")
                send_email_notification(user[0], user[1], scheduled_datetime)
        except Exception as e:
            print(f"Error sending email notification: {e}")
            # Continue even if email fails
            pass


        conn.close()
        return jsonify({'message': 'Schedule created successfully'}), 201

@app.route('/audssoncall/api/oncall/update', methods=['POST'])
def update_oncall_api():
    """
    API endpoint to trigger an on-call number update on all SBCs.
    """
    try:
        data = request.get_json()
        mobile_number = data.get('mobile')

        if not mobile_number:
            return jsonify({'status': 'error', 'message': 'Mobile number is required.'}), 400

        results = sbc_client.sbc_interaction(action='update', mobile=mobile_number)
        all_successful = all(result['status'] == 'success' for result in results)
        
        if all_successful:
            return jsonify({
                'status': 'success',
                'message': 'On-call number updated successfully on all SBCs.',
                'results': results
            }), 200
        else:
            return jsonify({
                'status': 'partial_success',
                'message': 'Some updates failed. Check individual results for details.',
                'results': results
            }), 207

    except Exception as e:
        print(f"Error in update_oncall_api: {e}")
        return jsonify({'status': 'error', 'message': 'An internal server error occurred.'}), 500
    
@app.route('/audssoncall/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    API endpoint to delete a user and their scheduled jobs.
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    
    try:
        sql_schedules = "DELETE FROM OnCallSchedules WHERE user_id = ?"
        cursor.execute(sql_schedules, (user_id,))
        
        sql_users = "DELETE FROM OnCallUsers WHERE id = ?"
        cursor.execute(sql_users, (user_id,))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            conn.close()
            return jsonify({'message': 'User and associated schedules deleted successfully.'}), 200
        else:
            conn.close()
            return jsonify({'error': 'User not found.'}), 404
            
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/audssoncall/api/schedule/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """API endpoint to delete a scheduled job."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    
    try:
        sql = "DELETE FROM OnCallSchedules WHERE id = ?"
        cursor.execute(sql, (schedule_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Schedule not found.'}), 404
        
        conn.close()
        return jsonify({'message': 'Scheduled job deleted successfully.'}), 200
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500


# --- SCHEDULER SETUP ---
if __name__ == '__main__':
    # scheduler = BackgroundScheduler(daemon=True)
    # scheduler.add_job(run_scheduled_updates, 'interval', minutes=5)
    # scheduler.start()
    app.run(debug=True)