import json
from typing import Optional
import markdown
from requests import Session
from fastapi import FastAPI, Request, Form, UploadFile, File,Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
# from git_workflow.pdf.test import kit_data
from slides.google_slide import create_speaker_kit_slides
from models.models import AgentResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import Column, Integer, String, DateTime, create_engine,Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import time
# from agent import team
from uuid import uuid4
from sqlalchemy import desc
import os, shutil 
from agents.speaker_platform_agent import agent as team
# from request_speaker_kit import request_speaker_kit
# from slides.slide import create_speaker_kit_slides

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# === Setup ===
app = FastAPI(root_path="/speaker-kit")
app.add_middleware(SessionMiddleware, secret_key="super-secret-y")
# Allow requests from your React frontend
origins = [
    "http://localhost:3000",  # React dev server
    "http://localhost:5173",  # if using Vite
    "http://127.0.0.1:3000",  # alternative
     "https://speaker-kit.testir.xyz",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow all origins
    allow_credentials=True,  # important if using session cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


app.mount("/static", StaticFiles(directory="static"), name="static")

# === Database Setup ===
DATABASE_URL = "sqlite:///./chat.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    # image_url = Column(String, nullable=False)
    # image_label=Column(String,nullable=False)
    # section=Column(String, nullable=False)
    sessionid = Column(String, unique=True, nullable=False)
    agent_session_id = Column(String, unique=True, nullable=True)
    title = Column(String, nullable=True)
    pdf_generated = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
class AgentResponse(Base):
    __tablename__ = "agent_responses"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False)
    output = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow  )


@app.get("/auth/check-session")
def check_session(request: Request):
    if "username" in request.session:
        return {"status": "ok"}
    return JSONResponse(status_code=401, content={"error": "Not logged in"})
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    user = Column(String, nullable=False)
    session_id=Column(String,nullable=False)
    message = Column(String, nullable=True)
    image = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# === Routes ===
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    username = request.session.get("username")
    sessionid = request.session.get("agentResponse", {}).get("output", {}).get("sessionid", "")
    if not username:
        return  templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("home.html", {"request": request,"username":username ,"sessionid":sessionid})
from pdf.app import create_speaker_kit_cover
@app.get("/auth/me")
async def read_users_me(request: Request):
    username = request.session.get("username")
    if not username:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    return {"username": username}

@app.post("/login")
async def login(request: Request, username: str = Form(...)):
    session_id = str(uuid4())
    request.session["username"] = username
    request.session["agentResponse"] = {"output": {"sessionid": session_id}}
    response = team.run("Let's start with Cover Page")
    print(response.__dict__)
    session = response.data.session_id
    message=response.data.output
    request.session["session"] = session
    db = SessionLocal()
    new_msg = ChatMessage(user="agent", message=message, image=None,session_id=session)
    db.add(new_msg)
    db.add(UserSession(username=username, sessionid=session_id,agent_session_id=session))
    db.commit()
    db.close()
    return  {"status": "ok","message":message}
    return RedirectResponse("/", status_code=200)

@app.post("/send")
async def send_message(request: Request, restart: bool = False, message: str = Form(""), file: Optional[UploadFile] = File(None), db: Session = Depends(get_db)):
    username = request.session.get("username")
    sessionid = request.session.get("agent_session_id")
    slides_url=""
    # dta=db.query(AgentResponse).filter(AgentResponse.session_id==sessionid).first()

    # if dta:
    #             pdf_path = f"static/Speaker_Kit_Cover_Two_Pages_Wide_Short{int(time.time())}.pdf"
    #             kit_data=json.loads(dta.output.replace("```json","").replace("```",''))
    #             create_speaker_kit_cover(
    #                 pdf_path=pdf_path,
    #                 bg_image_path="publicspeakerhero.jpeg",
    #                 headshot_path1=kit_data.get("headshots",""),
    #                 headshot_path=kit_data.get("headshots",""),
    #                 speaker_name=kit_data.get('name', 'Speaker Name'),
    #                 tagline=kit_data.get('tagline', 'Inspirational Speaker'),
    #                 tags=kit_data.get('professional_labels', 'Topic Expert'),
    #                 blur_radius=15,
    #                 about_text=kit_data.get('bio', 'About the speaker...'),
    #                 career_highlights=kit_data.get('career_highlights', [])
    #             )
    #             pdf_url = f"{base_url}/{pdf_path}"
    #             agent_message_content = f"\n\nCongratulations! Your speaker kit is ready. [Download PDF]({pdf_url})"
    #             db.add(ChatMessage(user="agent", message=agent_message_content, session_id=sessionid))
    #             db.commit()
    #             return {"message":f"\n\nCongratulations! Your speaker kit is ready. [Download PDF]({pdf_url})"}
    if not username:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    
    if not sessionid:
        return JSONResponse(status_code=400, content={"detail": "No active session"})

    base_url = str(request.base_url).rstrip("/")
    image_url = None
    original_message = message

    db_user_session = db.query(UserSession).filter(UserSession.agent_session_id == sessionid).first()
    last_message=db.query(ChatMessage).filter(ChatMessage.session_id==sessionid).order_by(desc(ChatMessage.timestamp)).first()
    if db_user_session and not db_user_session.title and original_message:
        db_user_session.title = original_message[:50]
        db.commit()

    if file and file.filename:
        ext = file.filename.split(".")[-1]
        filename = f"{uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        image_url = f"/static/uploads/{filename}"
        
        agent_input = f"{original_message}\n{base_url}{image_url}" if original_message else f"{base_url}{image_url}"
    else:
        agent_input = message
    
    db.add(ChatMessage(user=username, message=original_message, image=image_url, session_id=sessionid))
    db.commit()
    
    agent_response = team.run( agent_input, session_id=sessionid)
    # print(agent_response.__dict__)
    agent_message_content = agent_response.data.output
    print(agent_message_content)
    if  False:#"about what makes you differentsdasdsa".lower() in agent_message_content.lower():
        agent_message_content.replace("<!-- FINAL_STAGE:complete -->","")
        # headshot_message = db.query(ChatMessage).filter(ChatMessage.session_id == sessionid, ChatMessage.image.isnot(None)).order_by(desc(ChatMessage.timestamp)).first()
        if False:
            agent_message_content += "\n\nI'm ready to generate your speaker kit, but I need a headshot first. Please upload an image."
        else:
            try:
                # dta=db.query(AgentResponse).filter(AgentResponse.session_id==sessionid).first()
                # if dta:
                #   pdf_path = f"static/Speaker_Kit_Cover_Two_Pages_Wide_Short{int(time.time())}.pdf"
                #   kit_data=json.loads(dta.output.replace("```json","").replace("```",''))
                #   create_speaker_kit_cover(
                #     pdf_path=pdf_path,
                #     bg_image_path="publicspeakerhero.jpeg",
                #     headshot_path1=kit_data.get("headshots",""),
                #     headshot_path=kit_data.get("headshots",""),
                #     speaker_name=kit_data.get('name', 'Speaker Name'),
                #     tagline=kit_data.get('tagline', 'Inspirational Speaker'),
                #     tags=kit_data.get('professional_labels', 'Topic Expert'),
                #     blur_radius=15,
                #     about_text=kit_data.get('bio', 'About the speaker...'),
                #     career_highlights=kit_data.get('career_highlights', [])
                # )
                #   pdf_url = f"{base_url}/{pdf_path}"
                #   agent_message_content = f"\n\nCongratulations! Your speaker kit is ready. [Download PDF]({pdf_url})"
                #   db.add(ChatMessage(user="agent", message=agent_message_content, session_id=sessionid))
                #   db.commit()
                #   return {"message":f"\n\nCongratulations! Your speaker kit is ready. [Download PDF]({pdf_url})"}
                kitResponse = team.run(
            """extract data from the session in json format like 
               {"name":"[Name]" ,"email":"[Email]","website":"[website]","headshots":"[image_link_section_1]","heashot1":"[image_link_section2]", "tagline":"[tagline]","professional_labels":"[professional_labels]","bio":"[bio],"career_highlights":["[highlight1]","[highlight2]","[highlight3]"],"topics":[{"title":"[topic1_title]","description":"[topic1_description]","image":"[topic1_image]"},{"title":"[topic2_title]","description":"[topic2_description]","image":"[topic2_image]"}]}
               Instruction-> Return only json data no other words so it can be used by parsing and return empty on not able to extract or not available data.
            """, session_id=sessionid)
                # kit_data = request_speaker_kit(data.data.output)
                jsondata=(kitResponse.data.output.replace("```json","").replace("```",''))
                print(kitResponse)
                kit_data=json.loads(json.dumps(jsondata))
                pdf_path = f"static/Speaker_Kit_Cover_Two_Pages_Wide_Short{int(time.time())}.pdf"
                # headshot_image_path = headshot_message.image.lstrip('/')
                agent_response = AgentResponse(session_id=sessionid, output=json.dumps(jsondata))
                db.add(agent_response)
                db.commit()
                slides_url = create_speaker_kit_slides({
                "bg_image_path": "publicspeakerhero.jpeg",
                "headshot_path":kit_data.get("headshotss", 'https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D'),
                "name":kit_data.get("name","Sudarshan Shrestha"),
                "title":kit_data.get("tagline","Sudarshan Shrestha"),
                "tags":kit_data.get("professional_labels","Sudarshan Shrestha"),
                "bio": kit_data.get("bio","Sudarshan Shrestha"),
                "career_highlights":kit_data.get("bio", [
                    "Authored best-selling book 'The AI Alchemist: ' ",
                    "Keynote speaker at over 100 international conferences on AI and leadership,",
                    "Led a groundbreaking initiative that resulted in a 30% efficiency ",
                    "Recognized as 'Top Innovator in Tech' by TechForward Magazine (2023)  ",
                    "Founded a highly successful startup focused on ethical AI solutions,  ",
                    "Delivered a highly-rated TEDx talk on 'The Future of Human-AI Collaboration .",
                ]),
                "topics": kit_data.get("topics",[
                    {
                        "title": "AI Development",
                        "description": "AI Development focuses on the development of agents about AI. This topic is especially relevant due to the growing agents app development. The audience will gain the ability to build agentic frameworks and chat agents in real-time. The presentation style is interactive.",
                        "image": "https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D"
                    },
                    {
                        "title": "Flutter Development",
                        "description": "Flutter Development is about mobile app development. It's relevant due to growing business ideas. Attendees will learn to make their own app using Flutter. The talk is presented in an interactive style.",
                        "image": "https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D"
                    },
                    {
                        "title": "Python Development",
                        "description": "Python Development involves developing apps using Python frameworks. It's important now for real-time development of AI and agentic apps. The audience will learn to make real-time servers and apps. The presentation is motivational and career-driven.",
                        "image": "https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D"
                    },
                    {
                        "title": "Github",
                        "description": "Github focuses on learning git and development simultaneously while keeping track of changes. It's relevant due to tracking in the development of apps. The audience will gain skills in tracking and managing apps. The talk is presented in a research-based style.",
                        "image": "http://localhost:8000/static/uploads/e80697ad55234cce91b1695ad0fa3588.webp"
                    }
                ])
            })
                print("Slides created at:", slides_url)

                pdf_url = f"{base_url}/{pdf_path}"

                db_user_session.pdf_generated = True
                db.add(ChatMessage(user="agent", message=f"\n\nCongratulations! Your speaker kit is ready. [Download PDF]({slides_url})", session_id=sessionid))
                db.commit()
                return {"status": "ok","message":"message"}
            except Exception as e:
                print(f"Error generating PDF: {e}")
                return {"status":"error","message":"failed to generate pdf"}
    if slides_url:
        agent_message_content += f"\n\nCongratulations! Your speaker kit is ready. [Download PDF]({slides_url})"
    db.add(ChatMessage(user="agent", message=agent_message_content, session_id=sessionid))
    db.commit()

    return {"status": "ok","message":"message"}

@app.get("/request-pdf/{session_id}")
async def pdf_request(session_id: str,request: Request,db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id== session_id).all()
    # return messages
    # sessionid = request.session.get("session")
    data=team.run("""extract data from the session in json format like 
               {"name":"[Name]" ,"email":"[Email]","website":"[website]","headshots":"[image_link_section_1]","heashot1":"[image_link_section2]", "tagline":"[tagline]","subtagline":"[subtagline]","bio":"[about speaker],"career_highlights":["[highlight1]","[highlight2]","[highlight3]"],"topics":[{"title":"[topic1_title]","description":"[topic1_description]","image":"[topic1_image]"},{"title":"[topic2_title]","description":"[topic2_description]","image":"[topic2_image]"}]}
               Instruction-> Return only json data no other words so it can be used by parsing and return empty on not able to extract or not available data.Generate at least 6 carrer highlights,and bio should not be empty should be generate from about.Json should be able to load using json.loads([output]).Avoid adding lines
         """,session_id=session_id)
    kit_datas=data.data.output
    # Fix broken newlines inside the JSON string
    fixed_json = kit_datas 
    print(kit_datas)
    # with open("abc.json",'w')as f:
    #     f.write(kit_datas)
    print(fixed_json)
    agent_response = AgentResponse(session_id=session_id, output=kit_datas)
    db.add(agent_response)
    db.commit()

    # kit_data=request_speaker_kit(data.data.output)
    jsondata=(data.data.output)
    # print(json.loads(jsondata))
    # Step 1: Convert to dict
    # print(data.data.output['bio'])
    # Step 3: Convert back to dict via JSON
    # json_string = json.dumps(jsondata) 
    kit_data=None
    # print(jsondata)
    kit_data = json.loads(jsondata)
    # Add bio only if it is missing or empty
    if not kit_data.get("bio"):  # This covers both missing and empty string
        kit_data["bio"] = "This is a default bio describing the speaker's background and expertise."

    career_highlights = kit_data.get("career_highlights", [])

    # Pad to at least 6 items with empty strings
    while len(career_highlights) < 6:
        career_highlights.append("")
    slides_url = create_speaker_kit_slides({
                "bg_image_path": "publicspeakerhero.jpeg",
                "headshot_path":kit_data.get("headshotss", 'https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D'),
                "name":kit_data.get("name","Sudarshan Shrestha"),
                "title":kit_data.get("tagline","Sudarshan Shrestha"),
                "tags":kit_data.get("professional_labels","Sudarshan Shrestha"),
                "bio": kit_data.get("bio"," "),
                "career_highlights":kit_data.get("career_highlights", [
                    "Authored best-selling book 'The AI Alchemist: ' ",
                    "Keynote speaker at over 100 international conferences on AI and leadership,",
                    "Led a groundbreaking initiative that resulted in a 30% efficiency ",
                    "Recognized as 'Top Innovator in Tech' by TechForward Magazine (2023)  ",
                    "Founded a highly successful startup focused on ethical AI solutions,  ",
                    "Delivered a highly-rated TEDx talk on 'The Future of Human-AI Collaboration .",
                ]),
                "topics": kit_data.get("topics",[
                    {
                        "title": "AI Development",
                        "description": "AI Development focuses on the development of agents about AI. This topic is especially relevant due to the growing agents app development. The audience will gain the ability to build agentic frameworks and chat agents in real-time. The presentation style is interactive.",
                        "image": "https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D"
                    },
                    {
                        "title": "Flutter Development",
                        "description": "Flutter Development is about mobile app development. It's relevant due to growing business ideas. Attendees will learn to make their own app using Flutter. The talk is presented in an interactive style.",
                        "image": "https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D"
                    },
                    {
                        "title": "Python Development",
                        "description": "Python Development involves developing apps using Python frameworks. It's important now for real-time development of AI and agentic apps. The audience will learn to make real-time servers and apps. The presentation is motivational and career-driven.",
                        "image": "https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D"
                    },
                    {
                        "title": "Github",
                        "description": "Github focuses on learning git and development simultaneously while keeping track of changes. It's relevant due to tracking in the development of apps. The audience will gain skills in tracking and managing apps. The talk is presented in a research-based style.",
                        "image": "http://localhost:8000/static/uploads/e80697ad55234cce91b1695ad0fa3588.webp"
                    }
                ])
            })
    db.add(ChatMessage(user="agent", message=f"\n\nCongratulations! Your speaker kit is ready. [Download PDF]({slides_url})", session_id=session_id))
    db.commit()
    print("Slides created at:", slides_url)
    return {"message":slides_url}
    # Safely extract headshot URL if available
    # headshot_url = ""
    # try:
    #     headshot_url = kit_data.get('headshots', {}).get('headshot', {}).get('url', '')
    #     if headshot_url:
    #         if headshot_url.startswith('/static'):
    #             headshot_path = "static" + headshot_url.split("/static")[1]
    #         else:
    #             headshot_path = headshot_url
    #     else:
    #         headshot_path = ""
    # except Exception:
    #     headshot_path = ""

    # create_speaker_kit_cover(
    #     pdf_path=pdf_path,
    #     bg_image_path="publicspeakerhero.jpeg",  # Original unblurred image path
    #     headshot_path1=kit_data.get('images', {}),
    #     headshot_path=headshot_path,
    #     speaker_name=name,
    #     tagline=kit_data.get('tagline', 'Inspirational Speaker'),
    #     tags=kit_data.get('title', 'Topic Expert'),
    #     blur_radius=15,
    #     about_text=kit_data.get(
    #         'bio',
    #         (
    #             f"{name} is a visionary leader and acclaimed author, renowned for his "
    #             "transformative insights into modern leadership and technological innovation. "
    #             "With over two decades of experience, Jordan empowers organizations and individuals "
    #             "to navigate complex challenges and unlock their full potential in the digital age."
    #         )
    #     ),
    #     career_highlights=kit_data.get(
    #         'career_highlights',
    #         [
    #             "Authored best-selling book 'The AI Alchemist: ' ",
    #             "Keynote speaker at over 100 international conferences on AI and leadership,",
    #             "Led a groundbreaking initiative that resulted in a 30% efficiency ",
    #             "Recognized as 'Top Innovator in Tech' by TechForward Magazine (2023)  ",
    #             "Founded a highly successful startup focused on ethical AI solutions,  ",
    #             "Delivered a highly-rated TEDx talk on 'The Future of Human-AI Collaboration .",
    #         ]
    #     )
    # )
    return {"download_url": f"http://localhost:8000/{pdf_path}"}
    sessionid = request.session.get("session")
    messages = db.query(ChatMessage).filter(ChatMessage.session_id== sessionid).all()
    return messages
@app.get("/pdf")
async def get_messages(request: Request,db: Session = Depends(get_db)):
    sessionid = request.session.get("session")
    messages = db.query(ChatMessage).filter(ChatMessage.session_id== sessionid).order_by(desc(ChatMessage.timestamp)).first()
    response=team.run("Use collected data to crete a speaker kit in html.Do not provide any instruction or any text provide only html for speaker kit " ,session_id=sessionid)
    # print(messages.message)
    return HTMLResponse(
      
        response.data.output)
      

@app.get("/sessions")
def get_sessions(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    sessions = db.query(UserSession).filter(UserSession.username == username).order_by(desc(UserSession.timestamp)).all()
    # Return a list of conversations for the user
    return [{"id": s.agent_session_id, "title": s.title or f"Conversation from {s.timestamp.strftime('%Y-%m-%d %H:%M')}", "updated_at": s.timestamp.isoformat()} for s in sessions]
@app.post("/session/activate/{session_id}")
async def activate_session(session_id: str, request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    session_to_activate = db.query(UserSession).filter(UserSession.agent_session_id == session_id, UserSession.username == username).first()

    if not session_to_activate:
        return JSONResponse(status_code=404, content={"detail": "Session not found"})

    request.session["agent_session_id"] = session_id
    return {"status": "ok", "message": f"Session {session_id} activated."}
@app.post("/conversation/new")
async def new_conversation(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    session_id = str(uuid4())
    request.session["session_id"] = session_id

    # Start a new agent session
    response = team.run("Lets start.Begin with Cover Page ")
    agent_session_id = response.data.session_id
    message = response.data.output
    request.session["agent_session_id"] = agent_session_id

    try:
        user_session = UserSession(username=username, sessionid=session_id, agent_session_id=agent_session_id)
        db.add(user_session)

        new_msg = ChatMessage(user="agent", message=message, image=None, session_id=agent_session_id)
        db.add(new_msg)
        db.commit()
        db.refresh(user_session)
    finally:
        db.close()
    
    return {"status": "ok", "agent_session_id": agent_session_id}
@app.get("/session/{session_id}")
async def get_session(session_id: str,request: Request,db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id== session_id).all()
    return messages

