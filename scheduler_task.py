#scheduler_task.py

import pyodbc
import logging
import os
import sys
import smtplib
from datetime import datetime
from config import cfg
from sbcutils import PyRibbonClient
from email.message import EmailMessage

#Setup Log File
logfile = os.path.join(os.path.dirname(__file__), "audssoncall_scheduler.log")
if not os.path.exists(logfile):
    open(logfile, 'a').close()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logfile),
        logging.StreamHandler(sys.stdout)
    ]
)
logging.info("Scheduler task module loaded.")

#Function to Email User when schedule executed
def send_email_notification(user_name, mobile, scheduled_date):
    """Sends an email notification for a new schedule."""
    if not cfg.SMTP_SERVER:
        logging.warning("SMTP server not configured. Skipping email notification.")
        return

    msg = EmailMessage()
    msg.set_content(
        f"Hi you have been set as AUDSS on-call :\n\n"
        f"User: {user_name}\n"
        f"Mobile: {mobile}\n"
        f"Start of on Call Date: {scheduled_date.strftime('%Y-%m-%d %H:%M')}\n"
    )
    msg['Subject'] = 'You are on Call for AUDSS'
    msg['From'] = cfg.FROM_PERSON
    msg['To'] = user_name + "@transalta.com"
    msg['Cc'] = cfg.TO_PERSON
    logging.info(f"Emailing {msg['To']}")

    try:
        with smtplib.SMTP(cfg.SMTP_SERVER, cfg.SMTP_PORT) as s:
            s.starttls()
            s.send_message(msg)
        logging.info("Email notification sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def run_scheduled_updates():
    """
    Checks the database for pending schedules and triggers the SBC update.
    This function is intended to be run periodically by a scheduler.
    """
    logging.info("Running scheduled update check...")
    logging.info("Initialise SBC")
    sbvc_client = PyRibbonClient()
    logging.info("SBC Object Initialised")
    logging.info(f"DATABASE Connect {cfg.DB_SERVER}...")
    
    try:
        conn = pyodbc.connect(
            f'DRIVER={cfg.DB_DRIVER};'
            f'SERVER={cfg.DB_SERVER};'
            f'DATABASE={cfg.DB_NAME};'
            f'TRUSTED_CONNECTION={cfg.DB_TRUSTEDCONNECTION};'
        )
        conn.autocommit = True
        cursor = conn.cursor()
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return
    
    logging.info("Connected to the database.")
    # Find jobs that are due and pending
    sql = """
        SELECT s.id, u.mobile , s.scheduled_datetime
        FROM OnCallSchedules s
        JOIN OnCallUsers u ON s.user_id = u.id
        WHERE s.scheduled_datetime <= GETDATE() AND s.status = 'pending'
    """
    cursor.execute(sql)
    jobs_to_run = cursor.fetchall()
    logging.info(f"Found {len(jobs_to_run)} scheduled jobs to run.")
    if not jobs_to_run:
        logging.info("No scheduled jobs to run.")
        return
    
    for job in jobs_to_run:
        schedule_id, mobile_number , scheduled_datetime = job
        logging.info(f"Executing schedule ID {schedule_id} for number {mobile_number}")
        
        try:
            # Clean the mobile number and perform the update
            mobile = mobile_number.replace(" ", "")
            results = sbvc_client.sbc_interaction("update", mobile)
            logging.info(f"SBC update results for schedule ID {schedule_id}: {results}")
            
            # PATCH: Correctly iterate over the list to check for success
            is_successful = all(result.get('status') == 'success' for result in results)
            logging.info(f"All updates successful: {is_successful}")
            
            if is_successful:
                status = 'completed'
                print(f"Schedule ID {schedule_id} completed successfully.")
                # Send email notification
                cursor.execute("SELECT user_id FROM OnCallSchedules WHERE id = ?", schedule_id)
                user_id = cursor.fetchone()[0]
                cursor.execute("SELECT name FROM OnCallUsers WHERE id = ?", user_id)
                name = cursor.fetchone()[0]
                send_email_notification(name, mobile, scheduled_datetime)
                logging.info(f"Schedule ID {schedule_id} completed and email sent.")
            else:
                status = 'failed'
                print(f"Schedule ID {schedule_id} failed. Results: {results}")
                logging.error(f"Schedule ID {schedule_id} failed. Results: {results}")

            # Update the schedule status in the database
            cursor.execute("UPDATE OnCallSchedules SET status = ? WHERE id = ?", status, schedule_id)
            
        except Exception as e:
            print(f"An unexpected error occurred for schedule ID {schedule_id}: {e}")
            logging.error(f"An unexpected error occurred for schedule ID {schedule_id}: {e}")
            cursor.execute("UPDATE OnCallSchedules SET status = 'failed' WHERE id = ?", schedule_id)
            
    conn.close()

    #main
if __name__ == "__main__":
    run_scheduled_updates()
