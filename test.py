import json
import uuid
import os
from datetime import datetime
os.environ["TEAM_API_KEY"] = "faa44950238a5037b4bfd671106f8d95ad686a318b5c05afa525377f18ae7c45"
from aixplain.factories import AgentFactory, TeamAgentFactory
from textwrap import dedent
import os


# 📌 SESSION DIRECTORY
SESSION_DIR = "sessions"
os.makedirs(SESSION_DIR, exist_ok=True)


# 📁 SAVE FUNCTION
def save_session(session_id, data):
    with open(f"{SESSION_DIR}/{session_id}.json", "w") as f:
        json.dump(data, f)


# 📁 LOAD FUNCTION (optional)
def load_session(session_id):
    path = f"{SESSION_DIR}/{session_id}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


# ✨ CREATE AGENTS

cover_agent = AgentFactory.create(
    name="CoverPageAgent",
    description="Collects speaker cover page data",
    instructions=dedent("""
Hi there! 👋 I’m here to help you build your speaker kit. Let’s start with the cover page — this will make a bold first impression, so we want it to reflect your brand at its best. Ready? Let’s go.

Ask one question at a time:
[Section 1, Question 1] What’s your full name, exactly as you'd like it to appear on the cover?
[Section 1, Question 2] In one powerful sentence, what do you help people or companies do?
[Section 1, Question 3] What are a few short words or labels that describe you professionally?
[Section 1, Question 4] What’s your website or a contact email you’d like included?
[Section 1, Question 5] Please upload 1 great headshot — a clean, professional image of your face

Wrap up:
Thanks! That’s perfect for the cover page. When you're ready, we can move on to the next part About Speaker of your speaker kit.
""")
)

about_agent = AgentFactory.create(
    name="AboutSpeakerAgent",
    description="Collects bio and experience info",
    instructions=dedent("""
Let’s move on to your ‘About’ section — this is where we highlight your story, experience, and impact.

Ask one question at a time:
[Section 2, Question 1] What kind of work do you do most often?
[Section 2, Question 2] How many years have you been doing this kind of work?
[Section 2, Question 3] Roughly how many countries or cities have you spoken or worked in?
[Section 2, Question 4] Can you name a few big or meaningful clients or companies you’ve worked with?
[Section 2, Question 5] Do you have a personal mission or message that drives your work?
[Section 2, Question 6] Please upload a professional headshot — preferably one with a clean background or studio look.

Wrap up with a sample bio and ask for edits.
""")
)

topics_agent = AgentFactory.create(
    name="TopicsAgent",
    description="Develops speaker topics",
    instructions=dedent("""
Now let’s work on your speaking topics — the heart of your speaker kit.

[Section 3, Question 1] What are 3 to 5 topics you love talking about most?

For each topic, ask:
[Section 3, Question 2] What is this topic about?
[Section 3, Question 3] Why is this topic especially relevant or important right now?
[Section 3, Question 4] What does the audience gain or learn from this talk?
[Section 3, Question 5] Do you present it in a particular style or angle?
[Section 3, Question 6] Please upload a photo of you speaking — ideally one where you're mid-talk or engaging with an audience.

Wrap up and confirm everything reads well.
""")
)

export_agent = AgentFactory.create(
    name="ExportAgent",
    description="Final confirmation and export",
    instructions="All sections are complete and ready to export. 🎉\n\n**<!-- FINAL_STAGE:complete -->**"
)

# 🔁 Connect Agents via Team Agent

speaker_kit_team = TeamAgentFactory.create(
    name="SpeakerKitTeam",
    description="Multi-agent team to build a speaker kit",
    instructions=dedent("""
Ask each question one by one, tag with [Section X, Question Y], and transition to the next agent after each section. Mark the final step with **<!-- FINAL_STAGE:complete -->**
"""),
    agents=[cover_agent, about_agent, topics_agent, export_agent],
    # flow="CoverPageAgent -> AboutSpeakerAgent -> TopicsAgent -> ExportAgent"
)


# 💬 Chat Loop with Session Save

def run_chat():
    print("👋 Welcome to the Speaker Kit Builder Chat!")
    print("Type 'exit' to quit.\n")

    session_id = str(uuid.uuid4())
    session_data = {
        "session_id": session_id,
        "start_time": str(datetime.now()),
        "transcript": []
    }

    user_input = "Hi, I want to create my speaker kit."

    while True:
        response = speaker_kit_team.run(user_input)
        print("\n🤖 Agent:", response)
        session_data["transcript"].append({"agent": response.data.session_id})

        if "**<!-- FINAL_STAGE:complete -->**" in response:
            print("\n✅ Speaker kit generation complete!")
            break

        user_input = input("\n👤 Your answer: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye! 👋")
            break

        session_data["transcript"].append({"user": user_input})
        save_session(session_id, session_data)

    save_session(session_id, session_data)
    print(f"\n📝 Session saved as: {SESSION_DIR}/{session_id}.json")


if __name__ == "__main__":
    run_chat()
