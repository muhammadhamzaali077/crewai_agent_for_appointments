from crewai.flow.flow import Flow, start, listen, router
from litellm import completion
import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta


load_dotenv()

CALCOM_API_KEY = os.getenv("CALCOM_API_KEY")
CALCOM_BASE_URL = "https://api.cal.com/v1"
HEADERS = {"Content-Type": "application/json"}
QUERYSTRING = {"apiKey": CALCOM_API_KEY}


EVENT_TYPE = {'id': 1854515, 'title': 'AiCogniTech'}

def schedule_booking(event_id, name, email, start_time, location="inPerson", title="Meeting", description="", timezone="Asia/Karachi"):
    """Schedule a booking on Cal.com."""
    try:
        start_datetime = datetime.fromisoformat(start_time)
        end_datetime = start_datetime + timedelta(minutes=60)
        end_time = end_datetime.isoformat()

        url = f"{CALCOM_BASE_URL}/bookings"
        payload = {
            "eventTypeId": event_id,
            "start": start_time,
            "end": end_time,
            "responses": {
                "name": name,
                "email": email,
                "location": {
                    "optionValue": "",
                    "value": location
                }
            },
            "metadata": {},
            "timeZone": timezone,
            "language": "en",
            "title": title,
            "description": description,
            "status": "PENDING"
        }

        response = requests.post(url, headers=HEADERS, json=payload, params=QUERYSTRING)
        response.raise_for_status()

        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Agent: Error scheduling the booking: {e}")
        if e.response is not None:
            pass
        return None

def schedule_tool():
    """Interactive tool for scheduling a meeting."""
    print(f"\nAgent: Selected Event Type: {EVENT_TYPE['title']}")

    try:
        name = input("You: Enter your name: ").strip() or "Anonymous"
        email = input("You: Enter your email: ").strip() or "example@example.com"
        
        print("You: Enter your preferred meeting time:")
        year = int(input("  Year (e.g., 2025): ").strip())
        month = int(input("  Month (1-12): ").strip())
        day = int(input("  Day (1-31): ").strip())
        hour = int(input("  Hour (0-23): ").strip())
        minute = int(input("  Minute (0-59): ").strip())
        second = int(input("  Second (0-59): ").strip())
        gmt_offset = input("  GMT Offset (e.g., +05:00): ").strip()
        
        start_time = f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}{gmt_offset}"
        
        timezone = input("You: Enter your timezone (e.g., Asia/Karachi): ").strip() or "Asia/Karachi"
        
        location = input("You: Enter location (default: inPerson): ").strip() or "inPerson"
        title = input("You: Enter meeting title (default: Meeting): ").strip() or "Meeting"
        description = input("You: Enter description (default: Empty): ").strip() or ""

        result = schedule_booking(EVENT_TYPE['id'], name, email, start_time, location, title, description, timezone)
        if result:
            print("Agent: Booking successfully scheduled! Check your email for the confirmation and meeting details.")
        else:
            print("Agent: Failed to schedule the booking.")
    except Exception as e:
        print(f"Agent: Error: {e}")

class RoutedFlow(Flow):
    model = "gemini/gemini-1.5-flash"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    @start()
    def start_conversation(self):
        user_input = input("You: ").strip()
        self.state["user_input"] = user_input
        return user_input

    @router(start_conversation)
    def route_topic(self, user_input):
        if any(word in user_input.lower() for word in ["schedule", "book", "meeting", "appointment", "schedule a meeting", "schedule a meeting with", "schedule a meeting with me"]):
            return "schedule_route"
        else:
            return "conversation_route"

    @listen("schedule_route")
    def generate_schedule(self):
        print("Agent: Redirecting to the scheduling agent...")
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
    print("Agent: Welcome to AICongiTech! Redefining health and wellness with innovative AI solutions tailored for you. How may we assist you today?")
    flow = RoutedFlow()
    while True:
        try:
            output = flow.kickoff()
            if output and any(word in output.lower() for word in ["bye", "quit", "stop"]):
                print("Agent: Take care! See you soon!")
                break
        except Exception as e:
            print(f"Agent: ERROR: {e}")
            break

if __name__ == "__main__":
    main()
