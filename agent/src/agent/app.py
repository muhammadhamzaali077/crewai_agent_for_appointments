import streamlit as st
from datetime import datetime, timedelta
from crewai.flow.flow import Flow
from litellm import completion
import os
from dotenv import load_dotenv
import requests

load_dotenv()

CALCOM_API_KEY = os.getenv("CALCOM_API_KEY")
CALCOM_BASE_URL = "https://api.cal.com/v1"
HEADERS = {"Content-Type": "application/json"}
QUERYSTRING = {"apiKey": CALCOM_API_KEY}

EVENT_TYPE = {'id': 1854515, 'title': 'EngageAI'}

def initialize_chat_history():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": """Welcome to EngageAI! 🌟  

Hello! EngageAI specializes in crafting innovative AI-powered solutions tailored for HealthTech, AgeTech, FemTech, and Longevity industries. We excel in:  

- **AI-Driven Bots:** Intelligent automation to streamline operations.  
- **Multilingual Conversational AI:** Breaking language barriers for global reach.  
- **Personalized AI Strategies:** Accelerating market entry and enhancing operational efficiency.  

How can we assist you today? Whether you're exploring AI adoption or looking for bespoke AI strategies, we're here to guide you.
"""}
        ]

def schedule_booking(event_id, name, email, start_time, location="inPerson", title="Meeting", description="", timezone="Asia/Karachi"):
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
        return None

class StreamlitFlow(Flow):
    model = "gemini/gemini-2.0-flash"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    def process_user_input(self, user_input):
        if any(word in user_input.lower() for word in ["schedule", "book", "meeting", "appointment", "time slot", "event", "session", "booking"]):
            return "schedule_route"
        elif any(word in user_input.lower() for word in ["healthtech", "femtech", "longevity", "agetech", "services", "solutions", "ai", "automation"]):
            return "services_route"
        else:
            return "conversation_route"

    def handle_services_query(self, user_input):
        if "healthtech" in user_input.lower():
            return """In HealthTech, we deliver personalized AI models for patient care, operational efficiency, and predictive analytics. Examples include medical chatbots, appointment automation, and clinical decision support systems. How can we assist you in HealthTech?"""
        elif "femtech" in user_input.lower():
            return """In FemTech, we provide AI solutions like menstrual tracking, fertility optimization tools, and personalized wellness recommendations. Would you like to explore any of these areas further?"""
        elif "agetech" in user_input.lower() or "longevity" in user_input.lower():
            return """In AgeTech and Longevity, our AI solutions support healthy aging through predictive analytics, smart healthcare monitoring, and cognitive health enhancement tools. Let us know your interest!"""
        else:
            return """We offer a wide range of AI-powered solutions across HealthTech, FemTech, AgeTech, and Longevity. Would you like to:  
            1. Explore automation for your business?  
            2. Learn about multilingual conversational AI?  
            3. Discuss personalized AI strategies?  
            Let us know your focus area."""

    def handle_conversation(self, user_input):
        try:
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": user_input}],
                api_key=self.GEMINI_API_KEY
            )
            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    st.set_page_config(
        page_title="EngageAI",
        page_icon="🤖",
        layout="wide"
    )

    initialize_chat_history()
    flow = StreamlitFlow()

    # Custom CSS for prompt styling
    st.markdown("""
    <style>
        div[data-testid="stChatInput"] {
            position: fixed !important;
            bottom: 10px !important;
            left: 5%;
            width: 90%;
            background-color: #343a40;
            border-top: 1px solid #ddd;
            z-index: 1000;
            box-shadow: 0px -1px 5px rgba(0, 0, 0, 0.1);
        }
        div[data-testid="stChatInput"] input:focus {
            outline: none !important;
            box-shadow: 0px 0px 5px 2px orange !important;
            border: 1px solid orange !important;
            border-radius: 5px;
        }
        div[data-testid="stChatInput"] input {
            padding: 1px !important;
            width: 100% !important;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if prompt := st.chat_input("Type your message here..."):
            if st.session_state.get("awaiting_schedule_confirmation"):
                if prompt.lower() in ["yes", "yeah", "yep", "sure"]:
                    st.session_state.show_schedule_form = True
                    st.session_state.awaiting_schedule_confirmation = False
                else:
                    st.session_state.messages.append({"role": "assistant", "content": "Alright! Let us know if there's anything else we can assist you with."})
                    st.session_state.awaiting_schedule_confirmation = False
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                route = flow.process_user_input(prompt)

                if route == "schedule_route":
                    response = """Great! Let's schedule your meeting.

Here's what to do:
- Provide your name, email, date, and time.
- Choose whether to meet in person, online, or via phone.
- Add any extra details you'd like us to know.

Once Submitted:

- We'll book your appointment and send a confirmation email.
- If there's an issue, we'll follow up with alternatives.

Do you want to schedule an appointment?"""
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.session_state.awaiting_schedule_confirmation = True
                elif route == "services_route":
                    response = flow.handle_services_query(prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    response = flow.handle_conversation(prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response})

            st.rerun()

        if st.session_state.get("show_schedule_form", False):
            with st.chat_message("assistant"):
                st.markdown("### Schedule an Appointment")
                st.markdown("<div class='working-hours'>Our working hours are from 9:00 AM to 5:00 PM every day.</div>", unsafe_allow_html=True)
                st.markdown("\n")
                name = st.text_input("Name", placeholder="Enter your name")
                email = st.text_input("Email", placeholder="Enter your email")
                date = st.date_input("Preferred Date")
                time = st.time_input("Preferred Time")
                location = st.selectbox("Location", options=["inPerson", "online", "phone"])
                timezone = st.text_input("Timezone", value="Asia/Karachi")
                description = st.text_area("Description", placeholder="Additional details")

                if st.button("Submit Appointment"):
                    if not name or not email or not date or not time:
                        st.session_state.messages.append({"role": "assistant", "content": "Please fill in all required fields to schedule the appointment."})
                        st.rerun()
                    else:
                        start_time = f"{date}T{time.strftime('%H:%M:%S')}+05:00"
                        result = schedule_booking(EVENT_TYPE['id'], name, email, start_time, location, "Meeting", description, timezone)

                        if result:
                            confirmation_message = f"""
                            Appointment scheduled successfully! 🎉

                            **Details:**
                            - Name: {name}
                            - Date: {date}
                            - Time: {time.strftime('%H:%M:%S')} GMT+05:00
                            - Location: {location}

                            Please check your email ({email}) for confirmation details.
                            """
                            st.session_state.messages.append({"role": "assistant", "content": confirmation_message})
                        else:
                            st.session_state.messages.append({"role": "assistant", "content": "Failed to schedule the appointment. Please try again."})

                        st.session_state.show_schedule_form = False
                        st.rerun()

if __name__ == "__main__":
    main()
