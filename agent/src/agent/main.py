
from crewai.flow.flow import Flow, start, listen, router
from litellm import completion
import os
from dotenv import load_dotenv
import datetime as dt
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil import parser
from tzlocal import get_localzone
load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def main_func():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json")
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("src/agent/credentials.json", SCOPES)

            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    try:
        service = build("calendar", "v3", credentials=creds)
        now = dt.datetime.now().isoformat() + "Z"
        event_result = service.events().list(calendarId="primary", timeMin=now, maxResults=10, singleEvents=True, orderBy="startTime").execute()
        events = event_result.get("items", [])
        if not events:
            print("Not upcoming slots found")
            return
        for event in events:
            start = event["start"].get("datetime", event["start"].get("date"))
            print(start, event["summary"])       
    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main_func()

# def parse_datetime(input_str):
#     """
#     Parse user input into a proper datetime string.
#     Examples of input:
#       - "Tomorrow at 3 PM"
#       - "Next Monday 10 AM"
#       - "2025-02-15 14:00"
#     """
#     try:
#         return parser.parse(input_str).isoformat()
#     except Exception as e:
#         print(f"Invalid date format: {e}")
#         return None

# def create_appointment():
#     # Authenticate with Google Calendar API
#     flow = InstalledAppFlow.from_client_secrets_file('src/agent/credentials.json', SCOPES)
#     creds = flow.run_local_server(port=8080)
#     service = build('calendar', 'v3', credentials=creds)

#     # Detect user's local timezone
#     local_timezone = get_localzone().zone
#     print(f"Detected timezone: {local_timezone}")

#     # Collect user inputs
#     title = input("Enter the appointment title: ")
#     description = input("Enter a description: ")
#     location = "Karachi, Pakistan"

#     # Parse start date and time
#     while True:
#         start_time = parse_datetime(input("Enter the start time (e.g., 'Tomorrow at 3 PM'): "))
#         if start_time:
#             break

#     # Parse end date and time
#     while True:
#         end_time = parse_datetime(input("Enter the end time (e.g., 'Tomorrow at 4 PM'): "))
#         if end_time:
#             break

#     # Collect attendee email
#     attendee_email = input("Enter your email: ")

#     # Create an event
#     event = {
#         'summary': title,
#         'location': location,
#         'description': description,
#         'start': {'dateTime': start_time, 'timeZone': local_timezone},
#         'end': {'dateTime': end_time, 'timeZone': local_timezone},
#         'attendees': [{'email': attendee_email}],
#     }

#     # Insert the event
#     event = service.events().insert(calendarId='primary', body=event).execute()
#     print(f'Appointment created: {event.get("htmlLink")}')

# create_appointment()

# class RoutedFlow(Flow):
#     model = "gemini/gemini-1.5-flash"
#     GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


#     @start()
#     def generate_topic(self):
#         response = completion(
#             model=self.model,
#             messages=[{"role": "user", "content": "Generate a blog topic for 2025."}],
#             api_key=self.GEMINI_API_KEY
#         )
#         topic = response["choices"][0]["message"]["content"].strip()
#         # For demonstration, add a fake flag to the state.
#         self.state["is_tech"] = "tech" in topic.lower()
#         print(f"Topic: {topic}")
#         return topic

#     @router(generate_topic)
#     def route_topic(self):
#         # Route based on the is_tech flag.
#         if self.state.get("is_tech"):
#             return "tech_route"
#         else:
#             return "lifestyle_route"

#     @listen("tech_route")
#     def generate_tech_outline(self, topic):
#         response = completion(
#             model=self.model,
#             messages=[{"role": "user", "content": f"Create a detailed tech blog outline for: {topic}"}],
#             api_key=self.GEMINI_API_KEY
#         )
#         outline = response["choices"][0]["message"]["content"].strip()
#         print("Tech Outline:")
#         print(outline)
#         return outline

#     @listen("lifestyle_route")
#     def generate_lifestyle_outline(self, topic):
#         response = completion(
#             model=self.model,
#             messages=[{"role": "user", "content": f"Create a detailed lifestyle blog outline for: {topic}"}],
#             api_key=self.GEMINI_API_KEY
#         )
#         outline = response["choices"][0]["message"]["content"].strip()
#         print("Lifestyle Outline:")
#         print(outline)
#         return outline
# def kickoff():
#     flow = RoutedFlow()
# if __name__ == "__main__":
#     flow = RoutedFlow()
#     final_output = flow.kickoff()
#     print("Final Output:")
#     print(final_output)
