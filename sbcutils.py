# sbc_utils.py
import requests
import urllib3
import xml.etree.ElementTree as ET

from config import cfg

# Disable SSL warnings globally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PyRibbonClient:
    # ... (Your existing __init__, login, and close methods) ...
    def __init__(self):
        self.host = cfg.SBC_HOSTS
        self.username = cfg.SBC_USER
        self.password = cfg.SBC_PASS
        self.session = requests.Session()
        self.session.verify = False
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
            self.login(host)
            
            print(f"Checking on-call number for host: {host}")
            get_response = self.session.get(f"{base_url}/{q_resource}")
            get_response.raise_for_status()

            # Check for API status code in the XML response
            if self.check_api_status(get_response.text):
                response_text = get_response.text.strip()
                sbc_number = self.extract_outputfield_value(response_text)
                print(f"Extracted on-call number: {sbc_number} from host: {host}")
                
                return {
                    'host': host,
                    'status': 'success',
                    'number': sbc_number,
                    'message': f'Current on-call number: {sbc_number}'
                }
            else:
                return {'host': host, 'status': 'error', 'message': f'API error: Invalid response for {host}'}
        except (ConnectionError, requests.exceptions.RequestException) as e:
            print(f"Failed to retrieve on-call number for host {host}: {e}")
            return {'host': host, 'status': 'error', 'message': f'Failed to retrieve on-call number: {e}'}
        finally:
            try:
                self.session.post(f"https://{host}/rest/logout")
                print(f"Logged out of {host}")
            except Exception as e:
                print(f"Failed to logout of {host}: {e}")

    # Helper function to check for the XML status code
    def check_api_status(self, xml_string):
        """Checks for the presence of the expected data tag."""
        try:
            root = ET.fromstring(xml_string)
            # Check for the top-level transformationentry tag, which is not in a namespace.
            transformation_entry = root.find('transformationentry')
            
            if transformation_entry is not None:
                return True
            else:
                print(f"API Error XML: {xml_string}")
                return False
        except ET.ParseError as e:
            print(f"XML Parse Error: {e}")
            return False

    def update_oncall(self, host, new_mobile_number):
        """Updates the on-call number on a single SBC."""
        print(f"Updating on-call number for {host} to {new_mobile_number}")
        
        # Prepare the new mobile number
        clean_number = new_mobile_number.replace(" ", "")
        
        # Determine the correct API resource based on the host
        sbc_name = host.split('.')[0]
        if sbc_name == 'pernetgw01':
            q_resource = "transformationtable/20/transformationentry/9"
        elif sbc_name == 'parnetgw01':
            q_resource = "transformationtable/17/transformationentry/9"
        else:
            return {'host': host, 'status': 'error', 'message': 'Invalid host specified.'}

        # Check for empty mobile number
        if not clean_number:
            return {'host': host, 'status': 'error', 'message': 'Mobile number cannot be blank.'}

        # Create the data payload for the POST request
        resource_data = {'OutputFieldValue': f'+{clean_number}'}
        base_url = f"https://{host}/rest"

        try:
            self.login(host) # Log in to the SBC
            
            # Perform the update
            update_response = self.session.post(
                f"{base_url}/{q_resource}",
                data=resource_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            update_response.raise_for_status() # Raise an exception for bad status codes

            # Check for API status code in the XML response
            if self.check_api_status(update_response.text):
                # Optionally, re-check the number to confirm the update
                confirmed_number = self.extract_outputfield_value(update_response.text)
                
                if confirmed_number == f'+{clean_number}':
                    print(f"Successfully updated on-call number for {host}")
                    return {
                        'host': host,
                        'status': 'success',
                        'number': confirmed_number,
                        'message': f'Successfully updated on-call number to {confirmed_number}'
                    }
                else:
                    return {
                        'host': host,
                        'status': 'error',
                        'message': 'Update successful, but number mismatch confirmed.'
                    }
            else:
                return {'host': host, 'status': 'error', 'message': 'API error: Invalid response during update.'}

        except (ConnectionError, requests.exceptions.RequestException) as e:
            print(f"Failed to update on-call number for host {host}: {e}")
            return {'host': host, 'status': 'error', 'message': f'Failed to update on-call number: {e}'}
        finally:
            try:
                self.session.post(f"https://{host}/rest/logout")
                print(f"Logged out of {host}")
            except Exception as e:
                print(f"Failed to logout of {host}: {e}")

    def extract_outputfield_value(self, xml_string):
        """Extracts the output field value from the XML response."""
        try:
            root = ET.fromstring(xml_string)

            # Find the top-level element without a namespace.
            transformation_entry = root.find('transformationentry')

            if transformation_entry is not None:
                # Iterate through all children of transformation_entry to find the correct tag
                for child in transformation_entry:
                    if 'OutputFieldValue' in child.tag:
                        return child.text
                print("Error: Could not find OutputFieldValue tag within transformationentry.")
            else:
                print("Error: Could not find transformationentry tag.")
            return None

        except ET.ParseError as e:
            print(f"XML Parse Error: {e}")
            return None
        except Exception as e:
            print(f"Error extracting value: {e}")
            return None

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
    