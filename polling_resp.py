import requests
import time

AIXPLAIN_API_KEY = "faa44950238a5037b4bfd671106f8d95ad686a318b5c05afa525377f18ae7c45"
AGENT_ID = "6877e29acc93569ca54c127f"
POST_URL = f"https://platform-api.aixplain.com/sdk/agents/{AGENT_ID}/run"

headers = {
	"x-api-key": AIXPLAIN_API_KEY,
	"Content-Type": 'application/json'
}
def run_query(message, session_id=None):
    data = {
        "query": message,
    }

    if session_id:
        data["sessionId"] = session_id

    try:
        # Replace POST_URL and headers with your actual values
        response = requests.post(POST_URL, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        request_id = response_data.get("requestId")

        if not request_id:
            print("No requestId found in response:", response_data)
            return None

        get_url = f"https://platform-api.aixplain.com/sdk/agents/{request_id}/result"

        while True:
            get_response = requests.get(get_url, headers=headers)
            get_response.raise_for_status()
            result = get_response.json()

            if result.get("completed"):
                return result  # Return full result JSON
            else:
                time.sleep(3)
                return run_query(message=message,session_id=session_id)

    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
        return None