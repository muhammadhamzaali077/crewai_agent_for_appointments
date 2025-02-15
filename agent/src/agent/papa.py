from crewai.flow.flow import Flow, start, listen, router
from litellm import completion
import os
from dotenv import load_dotenv
import requests

load_dotenv()

# CALENDLY_API_KEY = os.getenv('CALENDLY_API_KEY')
CALENDLY_API_KEY = os.getenv("CALENDLY_API_KEY")

BASE_URL = "https://api.calendly.com"
headers = {"Authorization": f"Bearer {CALENDLY_API_KEY}"}

def get_user_uri():
    try:
        url = f"{BASE_URL}/users/me"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("resource", {}).get("uri")
    except requests.exceptions.RequestException as e:
        print(f"Agent: Error fetching user URI: {e}")
        return None

def get_event_types(user_uri):
    try:
        url = f"{BASE_URL}/event_types?user={user_uri}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        events = response.json().get("collection", [])
        return [{"name": event['name'], "uuid": event['uri'].split('/')[-1], "scheduling_url": event["scheduling_url"]}
            for event in events
            ]
    except requests.exceptions.RequestException as e:
        print(f"Agent: Error fetching event types: {e}")
        return None

def schedule_appointment(event_uuid, invitee_name, invitee_email):
    try:
        url = f"{BASE_URL}/scheduled_events/{event_uuid}/invitees"
        payload = {"email": invitee_email, "name": invitee_name}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            print("Agent: Meeting successfully scheduled.")
            return "Meeting successfully scheduled."
        else:
            print("Agent: Failed to schedule the meeting:", response.json())
            return "Failed to schedule the meeting."
    except requests.exceptions.RequestException as e:
        print(f"Agent: Error scheduling the meeting: {e}")
        return "Failed to schedule the meeting."

def schedule_tool():
    user_uri = get_user_uri()
    if user_uri:
        event_data = get_event_types(user_uri)
        if event_data:
            print("\nAgent: Available Events:")
            for i, event in enumerate(event_data):
                print(f"Agent: {i+1}. {event['name']}")
            try:
                choice = int(input("You: Enter the number of the event you want to schedule: ")) - 1
                if choice < 0 or choice >= len(event_data):
                    raise ValueError("Invalid choice.")
                selected_event = event_data[choice]
                invitee_name = input("You: Enter Your Name: ")
                invitee_email = input("You: Enter Your Email: ")
                return schedule_appointment(selected_event['uuid'], invitee_name, invitee_email)
            except (ValueError, IndexError):
                print("Agent: Invalid input. Please try again.")
                return None

class RoutedFlow(Flow):
    model = "gemini/gemini-1.5-flash"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    @start()
    def start_conversation(self):
        user_input = input("You: ").strip()
        print(f"Agent: Got it. Let me process that.")
        self.state["user_input"] = user_input
        return user_input

    @router(start_conversation)
    def route_topic(self, user_input):
        if any(word in user_input.lower() for word in ["schedule", "book", "meeting"]):
            return "schedule_route"
        else:
            return "conversation_route"

    @listen("schedule_route")
    def generate_schedule(self):
        print("Agent: Redirecting to the scheduling tool...")
        result = schedule_tool()
        return result

    @listen("conversation_route")
    def generate_conversation(self):
        user_input = self.state.get("user_input", "")
        response = completion(
            model=self.model,
            messages=[{"role": "user", "content": user_input}],
            api_key=self.GEMINI_API_KEY
        )
        outline = response["choices"][0]["message"]["content"].strip()
        print(f"Agent: {outline}")
        return outline
def main():
    print("Agent: Hello! How can I assist you today?")
    flow = RoutedFlow()
    while True:
        try:
            output = flow.kickoff()
            if "bye" in output.lower() or "quit" in output.lower() or "stop" in output.lower():
                print("Agent: Goodbye!")
                break
            print("Agent: What else can I do for you?")
        except Exception as e:
            print(f"Agent: ERROR: {e}")
            break
if __name__ == "__main__":
    main()