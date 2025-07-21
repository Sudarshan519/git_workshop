import requests
from google.oauth2 import service_account
import google.auth.transport.requests
import os # Import os module to handle file paths

def test_permissions():
    """
    Tests the permissions of a Google service account for Google Drive and Google Slides APIs.

    This function attempts to:
    1. Authenticate using a service account key file.
    2. Obtain an access token.
    3. Make a request to the Google Drive API to get user information.
    4. Make a request to the Google Slides API to create a new presentation.
    It prints the success or failure of each step.
    """
    
    # Define the path to your service account key file
    # Ensure this path is correct relative to where you run the script.
    SERVICE_ACCOUNT_FILE = 'service-account.json'
    
    # Define the necessary API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/presentations', # Scope for Google Slides API
        'https://www.googleapis.com/auth/drive'          # Scope for Google Drive API
    ]
    
    # Check if the service account file exists
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"❌ Error: Service account file not found at '{SERVICE_ACCOUNT_FILE}'")
        print("Please ensure the 'service-account.json' file is in the correct directory.")
        return

    try:
        # Authenticate the service account using the key file and defined scopes
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        # Create a request object for refreshing credentials
        auth_req = google.auth.transport.requests.Request()
        
        # Refresh the credentials to get an access token
        credentials.refresh(auth_req)
        access_token = credentials.token
        
        print("✅ Authentication successful")
        print(f"Access token: {access_token[:20]}...") # Print a truncated access token for security
        
        # Define headers for API requests, including the Authorization header with the access token
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # --- Test Google Drive API access ---
        drive_url = "https://www.googleapis.com/drive/v3/about"
        drive_params = {'fields': 'user'} # Request user information
        
        print("\nTesting Drive API...")
        # Make a GET request to the Drive API
        response = requests.get(drive_url, headers=headers, params=drive_params)
        print(f"Drive API response status code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Drive API access successful")
            print(f"User info: {response.json()}")
        else:
            print(f"❌ Drive API failed: {response.text}")
            
        # --- Test Google Slides API by creating a presentation ---
        slides_url = "https://slides.googleapis.com/v1/presentations"
        print("\nTesting Slides API (create presentation)...")
        
        # Define the request body for creating a new presentation
        body = {
            "title": "Test API Presentation" # Title of the new presentation
        }
        
        # Make a POST request to the Slides API to create a presentation
        response = requests.post(slides_url, headers=headers, json=body)
        print(f"Slides API create response status code: {response.status_code}")
        
        if response.status_code in (200, 201): # 200 OK or 201 Created
            print("✅ Slides API create successful")
            presentation_id = response.json().get("presentationId")
            print("Presentation ID:", presentation_id)
            # Grant writer permission to anyone with the link
            drive_permission_url = f"https://www.googleapis.com/drive/v3/files/{presentation_id}/permissions"
            permission_body = {
                "role": "writer",
                "type": "anyone"
            }
            perm_response = requests.post(drive_permission_url, headers=headers, json=permission_body)
            print(f"Permission response status code: {perm_response.status_code}")
            if perm_response.status_code in (200, 201):
                print("✅ Presentation is now editable by anyone with the link.")
            else:
                print(f"❌ Failed to set permission: {perm_response.text}")
        else:
            print(f"❌ Slides API create failed: {response.text}")
            
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc() # Print the full traceback for debugging

if __name__ == "__main__":
    test_permissions()
