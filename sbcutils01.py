# sbc_utils.py

import paramiko
#import pyribbon
import requests
import urllib3

from config import cfg

# Disable SSL warnings globally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PyRibbonClient:
    def __init__(self):
        self.host = cfg.SBC_HOSTS
        self.username = cfg.SBC_USER
        self.password = cfg.SBC_PASS
         # Create a single requests session to be reused
        self.session = requests.Session()
        self.session.verify = False # Set verification to False for all calls
        # Add authentication headers for all calls
        self.session.auth = (self.username, self.password)
        self.session.headers.update({
            'Accept': 'application/vnd.ribbon.elements+xml' 
        })

    def login(self, host):
        """Performs the login action to establish a session."""
        try:
            url = f"https://{host}/rest/login"
            auth = {"Username": self.username, "Password": self.password}
            headers = {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}
            
            response = self.session.post(url, data=auth, headers=headers)
            response.raise_for_status()
            
            # The SBC returns XML with the status code
            if '200' not in response.text:
                 raise requests.exceptions.HTTPError("Login failed: " + response.text)
                 
            print(f"Successfully logged into {host}")
            
        except requests.exceptions.RequestException as e:
            print(f"Login failed for {host}: {e}")
            raise ConnectionError(f"Login failed for {host}: {e}")
        
    # def session_creator(self, host):
    #     """Creates a pyribbon session for a given host."""
    #     try:
    #         print(f"Attempting to create session for host: {host}") # 1. Start of function
    #         session = pyribbon.pyribbon(host, self.username, self.password, verify=False)
    #         session.open()
    #         print(f"Session created successfully for host: {host}") # 2. Success
    #         return session
    #     except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
    #         # Handle network-related issues gracefully
    #         print(f"Network-related error occurred for host {host}: {e}")
    #         raise ConnectionError(f"Failed to connect to {host}: {e}")
    #     except Exception as e:
    #         # Catch all other exceptions
    #         print(f"Failed to create session with {host}: {e}")
    #         raise Exception(f"Failed to create session with {host}: {e}")

    
    # def check_oncall(self, host):
    #     """Checks the on-call number on a single SBC."""
    #     print("check_oncall called") # Add this line
    #     sbc_number = None
    #     sbc_name = host.split('.')[0]
    #     base_url = f"https://{host}/rest"

    #     if sbc_name == 'pernetgw01':
    #         q_resource = "transformationtable/20/transformationentry/9"
    #     elif sbc_name == 'parnetgw01':
    #         q_resource = "transformationtable/17/transformationentry/9"
    #     else:
    #         return {'host': host, 'status': 'error', 'message': 'Invalid host specified.'}

    #     try:
    #         print(f"Checking on-call number for host: {host}")
            
    #         # Use the requests session directly for the GET call
    #         get_response = self.session.get(f"{base_url}/{q_resource}")
    #         get_response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)

    #         response_text = get_response.text.strip()
    #         sbc_number = self.extract_outputfield_value(response_text)
    #         print(f"Extracted on-call number: {sbc_number} from host: {host}")
    #         return {
    #             'host': host,
    #             'status': 'success',
    #             'number': sbc_number,
    #             'message': f'Current on-call number: {sbc_number}'
    #         }
    #     except requests.exceptions.RequestException as e:
    #         # Catch all requests-related exceptions
    #         print(f"Failed to retrieve on-call number for host {host}: {e}")
    #         return {'host': host, 'status': 'error', 'message': f'Failed to retrieve on-call number: {e}'}

    def check_oncall(self, host):
        """Checks the on-call number on a single SBC."""
        print("check_oncall called")
        sbc_number = None
        sbc_name = host.split('.')[0]
        base_url = f"https://{host}/rest"

        if sbc_name == 'pernetgw01':
            q_resource = "transformationtable/20/transformationentry/9"
        elif sbc_name == 'parnetgw01':
            q_resource = "transformationtable/17/transformationentry/9"
        else:
            return {'host': host, 'status': 'error', 'message': 'Invalid host specified.'}

        try:
            self.login(host) # First, log in
            
            print(f"Checking on-call number for host: {host}")
            get_response = self.session.get(f"{base_url}/{q_resource}")
            get_response.raise_for_status()

            response_text = get_response.text.strip()
            sbc_number = self.extract_outputfield_value(response_text)
            print(f"Extracted on-call number: {sbc_number} from host: {host}")
            
            return {
                'host': host,
                'status': 'success',
                'number': sbc_number,
                'message': f'Current on-call number: {sbc_number}'
            }
        except (ConnectionError, requests.exceptions.RequestException) as e:
            print(f"Failed to retrieve on-call number for host {host}: {e}")
            return {'host': host, 'status': 'error', 'message': f'Failed to retrieve on-call number: {e}'}
        finally:
            try:
                # Add a logout function as well to clean up the session
                self.session.post(f"https://{host}/rest/logout")
                print(f"Logged out of {host}")
            except Exception as e:
                print(f"Failed to logout of {host}: {e}")

    def close(self):
        try:
            # Add verify=False here
            response = self.session.post(f"{self.url}/logout", verify=False)
            response.raise_for_status()
            return "ok"
        except Exception as e:
            # Handle potential logout failures gracefully
            print(f"Failed to gracefully log out: {e}")
            return "failed"

    def sbc_interaction(self, action, mobile=None):
        """
        Interacts with all SBCs based on the specified action.
        This replaces the old sbc_interaction function.
        """
        print(f"sbc_interaction called with action: {action}") # Add this line
        hosts = cfg.SBC_HOSTS
        results = []

        if action == "check":
            for host in hosts:
                result = self.check_oncall(host)
                results.append(result)
        elif action == "update":
            if not mobile:
                return {'status': 'error', 'message': 'Mobile number is required for update.'}
            for host in hosts:
                # Add logic to update the on-call number
                result = self.update_oncall(host, mobile)
                results.append(result)
                print(f"Update result for {host}: {result}")
        return results
    
    def extract_outputfield_value(self, xml_string):
        """Extracts the output field value from the XML response."""
        try:
            from xml.etree import ElementTree as ET
            root = ET.fromstring(xml_string)
            namespace = {'ns': 'http://www.sonusnet.com/schemas/ribbon/v1.0'}
            output_field = root.find('.//ns:outputField', namespace)
            if output_field is not None:
                return output_field.text
            return None
        except ET.ParseError:
            return None
        except Exception:
            return None