#config.py

import os
import yaml
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from io import StringIO  

# Load environment variables from .env file
load_dotenv()

#Read Config File
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

class Config:
        
    def __init__(self):
        self._password = self._getpassword()
        # # Database Configuration (using pyodbc)
        self.DB_DRIVER = config['DATABASE']['DRIVER']
        self.DB_SERVER = config['DATABASE']['SERVER']
        self.DB_NAME = config['DATABASE']['DATABASE']
        self.DB_TRUSTEDCONNECTION = config['DATABASE']['TRUSTEDCONNECTION']

        # # pyodbc connection string
        # SQLALCHEMY_DATABASE_URI = (
        #     f'mssql+pyodbc://{DB_USER}:{DB_PASS}@{DB_SERVER}/{DB_NAME}?'
        #     'driver=ODBC+Driver+17+for+SQL+Server'
        # )

        # SBC Configuration

        self.SBC_USER = config['SBC']['SBC_USER']
        #self.SBC_HOSTS = config['SBC']['SBC_HOST']
        self.SBC_HOSTS = ['pernetgw01.transalta.org', 'parnetgw01.transalta.org']
        self.SBC_PASS = self.password
        # Email Configuration

        self.SMTP_SERVER = config['MAIL']['SMTP_SERVER']
        self.SMTP_PORT = config['MAIL']['SMTP_PORT']
        self.TO_PERSON = config['MAIL']['TO_PERSON']
        self.FROM_PERSON = config['MAIL']['FROM_PERSON']
        self.EMAIL_SUBJECT = config['MAIL']['EMAIL_SUBJECT']
        
    def _decryptFile(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.key_path = os.path.join(script_dir, 'filekey.key')
        self.env_path = os.path.join(script_dir, '.env')
        # Open the keyfile
        #dir = os.path.dirname(__file__)
        #filekey = os.path.join(dir, 'filekey.key')
        try:
            with open(self.key_path, 'rb') as file:
                keyfile = file.read()
            # Open the envfile
            with open(self.env_path, 'rb') as file:
                encfile = file.read()
            # Create the decrypt object
            f_enc=Fernet(keyfile)
            # Decrpt the envfile
            decrypt = f_enc.decrypt(encfile)
            return decrypt
        except Exception as e:
            print("Opening Secure Connection", f"Decrpt Error: {e}" )
            return None   

    def _getpassword(self):
        try:
            decode = self._decryptFile().decode(encoding='cp1252')
            strIO = StringIO(decode)
            load_dotenv(stream=strIO)
            cred = os.environ.get('cred') 
            return cred          
        except Exception as e: 
           print("Opening Secure Connection", f"Decrpt Error: {e}" )
           return None
           
    @property
    def password(self):
        return self._password
 
cfg = Config() 
    

