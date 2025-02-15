from crewai.flow.flow import Flow, start, listen, router
from litellm import completion
import os
from dotenv import load_dotenv
import requests

load_dotenv()
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
    url = f"{BASE_URL}/event_types?user={user_uri}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        events = response.json().get("collection", [])
        return [
            {"name": event["name"], "uuid": event["uri"].split("/")[-1], "scheduling_url": event["scheduling_url"]}
            for event in events
        ]
    except requests.exceptions.RequestException as e:
        print(f"Agent: Failed to fetch event types. Error: {e}")
        return []

def schedule_tool():
    user_uri = get_user_uri()
    if user_uri:
        event_data = get_event_types(user_uri)
        if event_data:
            print("\nAvailable Events:")
            for i, event in enumerate(event_data):
                print(f"{i+1}. {event['name']}")
            try:
                choice = int(input("Enter the number of the event you want to schedule: ")) - 1
                if choice < 0 or choice >= len(event_data):
                    print("Agent: Invalid choice. Please try again.")
                    return
                selected_event = event_data[choice]

                # Display the scheduling link
                scheduling_url = selected_event["scheduling_url"]
                print(f"Open this Link to schedule meeting: {scheduling_url}")
            except ValueError:
                print("Agent: Invalid input. Please enter a number.")
        else:
            print("Agent: No events available to schedule.")
    else:
        print("Agent: Unable to fetch user URI.")

class RoutedFlow(Flow):
    model = "gemini/gemini-1.5-flash"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    @start()
    def start_conversation(self):
        user_input = input("You: ").strip()
        if not user_input:  # Ensure input is not empty
            print("Agent: Please say something to continue.")
            user_input = "default"  # Placeholder to avoid issues
        self.state["user_input"] = user_input
        return user_input

    @router(start_conversation)
    def route_topic(self, user_input):
        if not user_input:  # Ensure input is valid before processing
            print("Agent: Sorry, I didn't understand that.")
            return "conversation_route"

        if any(word in user_input.lower() for word in ["schedule", "book", "meeting"]):
            return "schedule_route"
        else:
            return "conversation_route"

    @listen("schedule_route")
    def generate_schedule(self):
        print("Agent: Redirecting to the scheduling tool...")
        schedule_tool()

    @listen("conversation_route")
    def generate_conversation(self):
        user_input = self.state.get("user_input", "")
        if not user_input:
            print("Agent: No input provided.")
            return

        try:
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": user_input}],
                api_key=self.GEMINI_API_KEY
            )
            outline = response["choices"][0]["message"]["content"].strip()
            print(f"Agent: {outline}")
            return outline
        except Exception as e:
            print(f"Agent: ERROR: {e}")

def main():
    print("Agent: Hello! How can I assist you today?")
    flow = RoutedFlow()
    while True:
        try:
            output = flow.kickoff()
            if output and any(word in output.lower() for word in ["bye", "quit", "stop"]):
                print("Agent: Goodbye!")
                break
        except Exception as e:
            print(f"Agent: ERROR: {e}")
            break

if __name__ == "__main__":
    main()
