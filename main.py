import json
import os
import shutil
from uuid import uuid4
from typing import Optional, List

from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from slides.google_slide import create_speaker_kit_slides
from agents.speaker_platform_agent import agent
from database.db import get_db, SessionLocal, engine
from models.models import UserSession, ChatMessage, AgentResponse, Base
from sqlalchemy.orm import Session as OrmSession
from difflib import SequenceMatcher

# === Setup ===
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-y",
    same_site="none",
    https_only=True
)

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "https://speaker-kit.testir.xyz",
    "https://speaker-kit-hotei1223s-projects.vercel.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

QUESTION_FLOW = [
    # Section 1 - Cover Page
    {"section": 1, "question": 1, "text": "What’s your full name, exactly as you'd like it to appear on the cover?"},
    {"section": 1, "question": 2, "text": "In one powerful sentence, what do you help people or companies do? (Think of it like a tagline – for example: ‘I help teams build unstoppable confidence in high-stakes situations.’)"},
    {"section": 1, "question": 3, "text": "What are a few short words or labels that describe you professionally? (For example: ‘Keynote Speaker | Author | Leadership Strategist’)"},
    {"section": 1, "question": 4, "text": "What’s your website or a contact email you’d like included?"},
    {"section": 1, "question": 5, "text": "Please upload 1 great headshot — a clean, professional image of your face"},

    # Section 2 - About the Speaker
    {"section": 2, "question": 1, "text": "What kind of work do you do most often? (For example: consulting, coaching, keynotes, innovation strategy, product development...)"},
    {"section": 2, "question": 2, "text": "How many years have you been doing this kind of work?"},
    {"section": 2, "question": 3, "text": "Roughly how many countries or cities have you spoken or worked in? (A range is fine — like ‘20+ countries’ or ‘30+ cities.’)"},
    {"section": 2, "question": 4, "text": "Can you name a few big or meaningful clients or companies you’ve worked with? (These could be well-known brands, mission-driven orgs, or any standout partnerships.)"},
    {"section": 2, "question": 5, "text": "Do you have a personal mission or message that drives your work? (For example: ‘I help people build courage in times of change’ or ‘I believe tech should serve humanity.’)"},
    {"section": 2, "question": 6, "text": "Please upload a professional headshot — preferably one with a clean background or studio look."},

    # Section 3 - Signature Speaking Topics
    {"section": 3, "question": 1, "text": "What are 3 to 5 topics you love talking about most? Just share the titles or main ideas — no need to get the wording perfect yet!"},
    {"section": 3, "question": 2, "text": "Great! Let’s go one by one and add more detail. Starting with: [insert first topic idea]"},
    {"section": 3, "question": 3, "text": "What is this topic about? (Give a 1–2 sentence explanation of the core idea.)"},
    {"section": 3, "question": 4, "text": "Why is this topic especially relevant or important right now?"},
    {"section": 3, "question": 5, "text": "What does the audience gain or learn from this talk?"},
    {"section": 3, "question": 6, "text": "Do you present it in a particular style or angle? (For example: story-driven, research-based, interactive, motivational?)"},
    {"section": 3, "question": 7, "text": "Please upload a photo of you speaking — ideally one where you're mid-talk or engaging with an audience."},

    # Section 4 - What Makes You Different
    {"section": 4, "question": 1, "text": "What do you think people like most about your talks, keynotes, or sessions?"},
    {"section": 4, "question": 2, "text": "What’s something unique about your delivery style — how you speak, teach, or engage an audience?"},
    {"section": 4, "question": 3, "text": "What do people often say after they’ve seen you speak or worked with you? (Think about compliments, audience reactions, or feedback you get often.)"},

    # Section 5 - Proof & Recognition
    {"section": 5, "question": 1, "text": "Have you ever written a book, been featured in the media, or spoken at a major event? (Name anything you remember — like TEDx talks, articles, panels, interviews, summits, etc.)"},
    {"section": 5, "question": 2, "text": "What 3 things are you most proud of in your professional life? (These can include leadership roles, recognitions, impact moments, or big clients — anything that makes you feel accomplished.)"},

    # Section 6 - Testimonials
    {"section": 6, "question": 1, "text": "Do you have any quotes or testimonials from past event organizers, clients, or audience members? (These could be formal or informal — even a compliment someone emailed you or said after a talk. If you know who said it and their role or organization, that’s even better!)"},
    {"section": 6, "question": 2, "text": "Perfect! Do you happen to know who each quote is from — and their title or company? Attribution makes them even more credible."},

    # Section 7 - Format & Contact
    {"section": 7, "question": 1, "text": "What kinds of talks or sessions do you offer? (Examples might include: 30–60 minute keynotes, workshops (half-day/full-day), panels, virtual sessions, private training, custom formats — whatever fits your style.)"},
    {"section": 7, "question": 2, "text": "Where should someone contact you to book you? (Please share your preferred email, website, calendar link, or any booking form — and let me know if you use a QR code for bookings.)"},
    {"section": 7, "question": 3, "text": "Is there anything else we haven’t covered that you think is important for your speaker kit?"},
    {"section": 7, "question": 4, "text": "Please upload any additional images or documents you’d like to include."},
    {"section": 7, "question": 5, "text": "Finally, please review your information. Is everything correct? (Reply with 'yes' to confirm or let me know what needs to be changed.)"}
]

# === Utility Functions ===

def get_next_question(asked_questions: List[str], section: int, question: int) -> Optional[dict]:
    for q in QUESTION_FLOW:
        qid = f"{q['section']}-{q['question']}"
        if qid not in asked_questions:
            return q
    return None

def is_relevant(user_message: str, question_text: str) -> bool:
    user_message = user_message.lower().strip()
    question_text = question_text.lower().strip()
    if not user_message or len(user_message) < 3:
        return False
    if 'upload' in question_text:
        return True
    ratio = SequenceMatcher(None, user_message, question_text).ratio()
    keywords = [w for w in question_text.split() if len(w) > 3]
    if any(k in user_message for k in keywords):
        return True
    return ratio > 0.2

def check_relevance_with_agent(question_text: str, user_message: str, sessionid: str) -> bool:
    prompt = (
        f"Is the following user response relevant to this question?\n"
        f"Question: {question_text}\n"
        f"User response: {user_message}\n"
        f"Respond only with 'yes' or 'no'."
    )
    response = agent.run(prompt, session_id=sessionid)
    print(response)
    answer = response.data.output.strip().lower()
    return answer.startswith("yes")

async def handle_file_upload(file, expects_upload, base_url):
    if file and file.filename and expects_upload:
        ext = file.filename.split(".")[-1]
        filename = f"{uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return base_url + f"/static/uploads/{filename}"
    return None

# === Section Handlers ===

async def handle_topic_flow(message, db, user_session, asked_questions, sessionid, username, image):
    if not getattr(user_session, 'topics', None):
        if user_session.current_question == 1:
            topics = [t.strip() for t in message.split(',') if t.strip()]
            user_session.topics = json.dumps(topics)
            user_session.current_topic_index = 0
            db.commit()
    topics = json.loads(user_session.topics or "[]")
    current_topic_index = getattr(user_session, 'current_topic_index', 0)
    topic_qs = [2, 3, 4, 5, 6]
    topic_total = len(topics)

    t_idx = current_topic_index
    if t_idx < topic_total:
        for tq in topic_qs:
            qid = f"3-{tq}-topic{t_idx}"
            if qid not in asked_questions:
                q_obj = next(q for q in QUESTION_FLOW if q["section"] == 3 and q["question"] == tq)
                q_text = f"{q_obj['text']} ({topics[t_idx]})"
                asked_questions.append(qid)
                user_session.asked_questions = json.dumps(asked_questions)
                user_session.current_section = 3
                user_session.current_question = tq
                db.add(ChatMessage(user=username, message=message, image=image, session_id=sessionid, section=3, is_question=False,))
                db.commit()
                agent_response = agent.run(
                    f"Take '{message}' as user answer. Ask next question: {q_text}", session_id=sessionid
                )
                print(agent_response)
                db.add(ChatMessage(user="agent", message=agent_response.data.output, is_question=True, section=3, session_id=sessionid))
                db.commit()
                return {
                    "status": "ok",
                    "message": agent_response.data.output,
                    "current_section": 3,
                    "current_question": tq,
                    "current_topic": topics[t_idx],
                    "current_topic_index": t_idx
                }
        user_session.current_topic_index = t_idx + 1
        db.commit()
        user_session.current_section = 4
        user_session.current_question = 1
        db.commit()

    ready_key = f"ready_for_section_{user_session.current_section}"
    next_section = user_session.current_section + 1
    if hasattr(user_session, ready_key) and getattr(user_session, ready_key) is False:
        if message.strip().lower() in ["yes", "y", "ready", "let's go", "continue", "next"]:
            setattr(user_session, ready_key, True)
            user_session.current_section = next_section
            user_session.current_question = 1
            db.commit()
        else:
            return {"status": "wait", "message": f"Let me know when you're ready to move to Section {next_section}."}
    if not hasattr(user_session, ready_key):
        setattr(user_session, ready_key, False)
        db.commit()
    ready_val = getattr(user_session, ready_key)
    if ready_val is False:
        if message.strip().lower() in ["yes", "y", "ready", "let's go", "continue", "next"]:
            setattr(user_session, ready_key, True)
            user_session.current_section = next_section
            user_session.current_question = 1
            db.commit()
        else:
            return {"status": "wait", "message": f"Let me know when you're ready to move to Section {next_section}."}
    return {"status": "section_complete", "message": f"You've completed Section {user_session.current_section - 1}. Are you ready to move to Section {user_session.current_section}? (yes/no)"}

async def handle_non_topic_section_flow(message, db, user_session, asked_questions, sessionid, username, image):
    current_section = user_session.current_section
    current_question = user_session.current_question

    def section_questions(section):
        return [q for q in QUESTION_FLOW if q.get("section") == section]
    section_qs = section_questions(current_section)
    section_qids = [f"{q['section']}-{q['question']}" for q in section_qs]
    section_done = all(qid in asked_questions for qid in section_qids)

    # Only handle section advancement if all questions in the section are done
    if section_done:
        ready_key = f"ready_for_section_{current_section+1}"
        if not hasattr(user_session, ready_key):
            setattr(user_session, ready_key, False)
            db.commit()
        ready_val = getattr(user_session, ready_key)
        if ready_val is False:
            if message.strip().lower() in ["yes", "y", "ready", "let's go", "continue", "next", "ok", "done"]:
                setattr(user_session, ready_key, True)
                user_session.current_section += 1
                user_session.current_question = 1
                db.commit()
                next_q = get_next_question(asked_questions, user_session.current_section, user_session.current_question)
                if next_q:
                    return {
                        "status": "ok",
                        "message": next_q['text'],
                        "current_section": next_q['section'],
                        "current_question": next_q['question']
                    }
                else:
                    return {"status": "done", "message": "All questions completed!"}
            else:
                return {"status": "section_complete", "message": f"You've completed Section {current_section}. Are you ready to move to Section {current_section+1}? (yes/no)"}

    next_q = get_next_question(asked_questions, current_section, current_question)
    if not next_q:
        data = agent.run(
            """extract data from the session in json format like 
               {\"name\":\"[Name]\" ,\"email\":\"[Email]\",\"website\":\"[website]\",\"headshots\":\"[image_link_section_1]\",\"heashot1\":\"[image_link_section2]\", \"tagline\":\"[tagline]\",\"subtagline\":\"[subtagline]\",\"bio\":\"[bio],\"career_highlights\":[\"[highlight1]\",\"[highlight2]\",\"[highlight3]\"],\"topics\":[{\"title\":\"[topic1_title]\",\"description\":\"[topic1_description]\",\"image\":\"[topic1_image]\"},{\"title\":\"[topic2_title]\",\"description\":\"[topic2_description]\",\"image\":\"[topic2_image]\"}]}
               Instruction-> Return only json data no other words so it can be used by parsing and return empty on not able to extract or not available data.
            """, session_id=sessionid)
        agent_response = AgentResponse(session_id=sessionid, output=data.data.output)
        db.add(agent_response)
        db.commit()
        return {"status": "done", "message": "All questions completed!", "extracted_data": data.data.output}

    qid = f"{next_q['section']}-{next_q['question']}"
    if qid in asked_questions:
        return {"status": "repeat", "message": "This question has already been asked."}

    asked_questions.append(qid)
    user_session.asked_questions = json.dumps(asked_questions)
    user_session.current_section = next_q['section']
    user_session.current_question = next_q['question']
    db.commit()
    prompt = (
        f"Previous user response: {message}\n"
        f"Now, ask the following question to the user:\n"
        f"{next_q['text']}"
    )
    agent_response = agent.run(prompt, session_id=sessionid)
    print(agent_response)
    db.add(ChatMessage(user=username, message=message, image=image, session_id=sessionid))
    db.commit()
    db.add(ChatMessage(user="agent", message=next_q['text'], is_question=True, section=next_q['section'], session_id=sessionid))
    db.commit()
    return {
        "status": "ok",
        "message": agent_response.data.output,
        "current_section": next_q['section'],
        "current_question": next_q['question']
    }

# === Routes ===

@app.get("/auth/check-session")
def check_session(request: Request):
    if "username" in request.session:
        return {"status": "ok"}
    return JSONResponse(status_code=401, content={"error": "Not logged in"})

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    username = request.session.get("username")
    sessionid = request.session.get("agentResponse", {}).get("output", {}).get("sessionid", "")
    if not username:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("home.html", {"request": request, "username": username, "sessionid": sessionid})

@app.post("/login")
async def login(request: Request, username: str = Form(...)):
    session_id = str(uuid4())
    request.session["username"] = username
    request.session["agentResponse"] = {"output": {"sessionid": session_id}}
    response = agent.run("Let's start")
    session = response.data.session_id
    request.session["session"] = session
    db = SessionLocal()
    db.add(UserSession(username=username, sessionid=session_id, agent_session_id=session))
    db.commit()
    db.close()
    return {"status": "ok", "message": "ok"}

@app.get("/auth/me")
async def read_users_me(request: Request):
    username = request.session.get("username")
    if not username:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    return {"username": username}

@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"status": "ok", "message": "Logged out"}

@app.post("/send")
async def send_message(
    request: Request,
    message: str = Form(""),
    file: Optional[UploadFile] = File(None),
    db: OrmSession = Depends(get_db),
):
    username = request.session.get("username")
    sessionid = request.session.get("session")
    base_url = str(request.base_url).rstrip("/")
    image = None

    user_session = db.query(UserSession).filter(UserSession.agent_session_id == sessionid).first()
    if not user_session:
        return {"status": "error", "message": "Session not found"}

    asked_questions = json.loads(user_session.asked_questions) if user_session.asked_questions else []
    current_section = user_session.current_section or 1
    current_question = user_session.current_question or 1

    q_obj = next((q for q in QUESTION_FLOW if q.get("section") == current_section and str(q.get("question")) == str(current_question)), None)
    expects_upload = q_obj and "upload" in q_obj["text"].lower()
    image = await handle_file_upload(file, expects_upload, base_url)

    # Check if user is being prompted to move to next section and replied "yes"
    ready_key = f"ready_for_section_{current_section+1}"
    
    if hasattr(user_session, ready_key) and getattr(user_session, ready_key) is False:
        if message.strip().lower() in ["yes", "y", "ready", "let's go", "continue", "next", "ok", "done"]:
            setattr(user_session, ready_key, True)
            user_session.current_section += 1
            user_session.current_question = 1
            db.commit()
            # Reset asked_questions for new section if needed
            return await handle_non_topic_section_flow(
                message, db, user_session, asked_questions, sessionid, username, image
            )
        else:
            return {"status": "wait", "message": f"Let me know when you're ready to move to Section {current_section+1}."}

    if current_section == 3:
        return await handle_topic_flow(
            message, db, user_session, asked_questions, sessionid, username, image
        )
    return await handle_non_topic_section_flow(
        message, db, user_session, asked_questions, sessionid, username, image
    )

@app.get('/request-pdf')
def get_mess(request: Request, db: OrmSession = Depends(get_db)):
    kit_data = {
        "name": "Sudarshan Shrestha",
        "email": "",
        "website": "sudarshan.vercel.app",
        "headshots": "https://adbb25181c7d.ngrok-free.app/static/uploads/71eed53e49b64e83acdf6ebe4b74bf4a.jpg",
        "heashot1": "http://localhost:8000/static/uploads/2cb320ab3a614a319c56d703f6c27737.webp",
        "tagline": "I help teams build unstoppable confidence in high-stakes situations",
        "subtagline": "Keynote Speaker | Author | Leadership Strategist",
        "bio": "Sudarshan Shrestha is a Keynote Speaker | Author | Leadership Strategist who helps teams build unstoppable confidence in high-stakes situations. With over 10 years of experience in coaching, he has worked in 30+ cities, collaborating with clients like AI District Agents and Industry Rockstar to drive impactful change. Known for his belief that tech should serve humanity, he is also an author. His mission is to empower people through technology.",
        "career_highlights": [
            "Over 10 years of coaching experience",
            "Worked in 30+ cities",
            "Clients include AI District Agents and Industry Rockstar"
        ],
        "topics": [
            {
                "title": "AI Development",
                "description": "AI Development focuses on the development of agents about AI. This topic is especially relevant due to the growing agents app development. The audience will gain the ability to build agentic frameworks and chat agents in real-time. The presentation style is interactive.",
                "image": "http://localhost:8000/static/uploads/0d07b84226384b5a9a5b06670c6c6d90.png"
            },
            {
                "title": "Flutter Development",
                "description": "Flutter Development is about mobile app development. It's relevant due to growing business ideas. Attendees will learn to make their own app using Flutter. The talk is presented in an interactive style.",
                "image": "http://localhost:8000/static/uploads/072fb7183f374bd6a60468fa2e7f7854.png"
            },
            {
                "title": "Python Development",
                "description": "Python Development involves developing apps using Python frameworks. It's important now for real-time development of AI and agentic apps. The audience will learn to make real-time servers and apps. The presentation is motivational and career-driven.",
                "image": "https://adbb25181c7d.ngrok-free.app/static/uploads/5288892a699441ff84de380fdd5c4c5b.png"
            },
            {
                "title": "Github",
                "description": "Github focuses on learning git and development simultaneously while keeping track of changes. It's relevant due to tracking in the development of apps. The audience will gain skills in tracking and managing apps. The talk is presented in a research-based style.",
                "image": "https://adbb25181c7d.ngrok-free.app/static/uploads/e80697ad55234cce91b1695ad0fa3588.webp"
            }
        ]
    }
    slides_url = create_speaker_kit_slides(kit_data)
    return {"download_url": f"{slides_url}"}

@app.get("/messages")
async def get_messages(request: Request, db: OrmSession = Depends(get_db), group_by_section: bool = False):
    sessionid = request.session.get("session")
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == sessionid).all()
    msg_dicts = [
        {
            "id": m.id,
            "user": m.user,
            "session_id": m.session_id,
            "message": m.message,
            "image": m.image,
            "is_question": m.is_question,
            "section": m.section,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None
        }
        for m in messages
    ]
    if group_by_section:
        grouped = {}
        for msg in msg_dicts:
            sec = msg["section"] or "Uncategorized"
            grouped.setdefault(sec, []).append(msg)
        return grouped
    return msg_dicts

@app.get("/sessions")
def get_sessions(db: OrmSession = Depends(get_db)):
    sessions = db.query(UserSession).all()
    db.close()
    return [{"username": s.username, "sessionid": s.sessionid, "timestamp": s.timestamp.isoformat()} for s in sessions]

@app.get("/session/{session_id}")
async def get_session(session_id: str, request: Request, db: OrmSession = Depends(get_db), group_by_section: bool = False):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
    msg_dicts = [
        {
            "id": m.id,
            "user": m.user,
            "session_id": m.session_id,
            "message": m.message,
            "image": m.image,
            "is_question": m.is_question,
            "section": m.section,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None
        }
        for m in messages
    ]
    if group_by_section:
        grouped = {}
        for msg in msg_dicts:
            sec = msg["section"] or "Uncategorized"
            grouped.setdefault(sec, []).append(msg)
        return grouped
    return msg_dicts
