#scheduler_task.py

import pyodbc
from datetime import datetime
from config import Config , cfg
from sbcutils import PyRibbonClient

def run_scheduled_updates():
    """
    Checks the database for pending schedules and triggers the SBC update.
    This function is intended to be run periodically by a scheduler.
    """
    
    sbvc_client = PyRibbonClient()
    print(f"[{datetime.now()}] Running scheduled update check...")
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={cfg.DB_SERVER};'
        f'DATABASE={cfg.DB_NAME};'
        f'TRUSTED_CONNECTION={cfg.DB_TRUSTEDCONNECTION};'
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # Find jobs that are due and pending
    sql = """
        SELECT s.id, u.mobile
        FROM OnCallSchedules s
        JOIN OnCallUsers u ON s.user_id = u.id
        WHERE s.scheduled_datetime <= GETDATE() AND s.status = 'pending'
    """
    cursor.execute(sql)
    jobs_to_run = cursor.fetchall()

    if not jobs_to_run:
        print("No scheduled jobs to run.")
        return

    for job in jobs_to_run:
        schedule_id, mobile_number = job
        print(f"Executing schedule ID {schedule_id} for number {mobile_number}")
        
        try:
            # Clean the mobile number and perform the update
            mobile = mobile_number.replace(" ", "")
            results = sbvc_client.sbc_interaction(mobile, action="update")
            
            # Check if all updates were successful
            is_successful = all(result.get('status') == 'success' for result in results.values())
            
            if is_successful:
                status = 'completed'
                print(f"Schedule ID {schedule_id} completed successfully.")
            else:
                status = 'failed'
                print(f"Schedule ID {schedule_id} failed. Results: {results}")

            # Update the schedule status in the database
            cursor.execute("UPDATE OnCallSchedules SET status = ? WHERE id = ?", status, schedule_id)
            
        except Exception as e:
            print(f"An unexpected error occurred for schedule ID {schedule_id}: {e}")
            cursor.execute("UPDATE OnCallSchedules SET status = 'failed' WHERE id = ?", schedule_id)
            
    conn.close()