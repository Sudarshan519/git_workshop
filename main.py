import json
from typing import Optional
import markdown
from requests import Session
import requests
from fastapi import FastAPI, Request, Form, UploadFile, File,Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import Column, Integer, String, DateTime, create_engine,Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import time
from uuid import uuid4
from sqlalchemy import desc
import os, shutil 
from agents.speaker_platform_agent import agent
from aixplain.modules.agent import OutputFormat
# from request_speaker_kit import request_speaker_kit

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database.db import get_db, SessionLocal, engine
from models.models import UserSession, ChatMessage, AgentResponse,Base
# create all tables if they don't exist
Base.metadata.create_all(bind=engine)
# === Setup ===
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret-y")
# Allow requests from your React frontend
origins = [
    "http://localhost:3000",  # React dev server
    "http://localhost:5173",  # if using Vite
    "http://127.0.0.1:3000",  # alternative
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



@app.get("/auth/check-session")
def check_session(request: Request):
    if "username" in request.session:
        return {"status": "ok"}
    return JSONResponse(status_code=401, content={"error": "Not logged in"})


# === Routes ===
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    username = request.session.get("username")
    sessionid = request.session.get("agentResponse", {}).get("output", {}).get("sessionid", "")
    if not username:
        return  templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("home.html", {"request": request,"username":username ,"sessionid":sessionid})
from pdf.app import create_speaker_kit_cover

@app.post("/login")
async def login(request: Request, username: str = Form(...)):
    session_id = str(uuid4())
    request.session["username"] = username
    request.session["agentResponse"] = {"output": {"sessionid": session_id}}
    response = agent.run("Let's start")
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
async def send_message(request: Request,restart:bool=False, message: str = Form(""), file: Optional[UploadFile] = File(None),db: Session = Depends(get_db),q: Optional[str] = Query(None, min_length=3, alias="query")):
    username = request.session.get("username")
    sessionid = request.session.get("session")
    base_url = str(request.base_url).rstrip("/")
    print(sessionid)
    image=None
    response=None
    if restart:
        response = agent.run("Let's start")
        session_id = str(uuid4())
        request.session["username"] = username
        request.session["agentResponse"] = {"output": {"sessionid": session_id}}
        response = agent.run("Let's start")
        session = response.data.session_id
        message=response.data.output
        request.session["session"] = session
        db = SessionLocal()
        new_msg = ChatMessage(user="agent", message=message, image=None,session_id=session)
        db.add(new_msg)
        db.add(UserSession(username=username, sessionid=session_id,agent_session_id=session))
        db.commit()
        db.close()
        return {"status": "ok","message":message}
    if not username:
      session_id = str(uuid4())
      request.session["username"] = username
      request.session["agentResponse"] = {"output": {"sessionid": session_id}}
      response = agent.run("Let's start")
      session = response.data.session_id
      message=response.data.output
      request.session["session"] = session
      db = SessionLocal()
      new_msg = ChatMessage(user="agent", message=message, image=None,session_id=session)
      db.add(new_msg)
      db.add(UserSession(username=username or '', sessionid=session_id,agent_session_id=session))
      db.commit()
      db.close()
      return {"status": "ok","message":message}
  
    #   return {}
    
    if file and file.filename : 
        ext = file.filename.split(".")[-1]
        filename = f"{uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        image =base_url+ f"/static/uploads/{filename}"
        print(image)
        response=agent.run(image,session_id=sessionid)
        
    else:
        response=agent.run(message,session_id=sessionid)
        print(response.data.output)
        # message=response.data.output
    data = {"user": "agent", "message":message , "image": None,"session_id":sessionid}
    # insert user message
    new_msg = ChatMessage(user=username, message=message, image=image,session_id=sessionid)
    db.add(new_msg)
    db.commit()
    db.close()
    # save agent response to database
    new_msg = ChatMessage(user= "agent", message=response.data.output, session_id=sessionid)
    db.add(new_msg)
    db.commit()
    message=markdown.markdown(response.data.output) 
    # if "Do you have a personal mission" in message:
    session_data=db.query(UserSession).filter(UserSession.agent_session_id == sessionid) .first() 
    if message.__contains__("a professional headshot") or message.__contains__("Please upload a professional headshot"):
        
        session_data.pdf_ready=True
        db.commit()
    if session_data.pdf_ready:
        data = agent.run(
            """extract data from the session in json format like 
               {"name":"[Name]" ,"email":"[Email]","website":"[website]","headshots":"[image_link_section_1]","heashot1":"[image_link_section2]", "tagline":"[tagline]","subtagline":"[subtagline]","bio":"[bio],"career_highlights":["[highlight1]","[highlight2]","[highlight3]"],"topics":[{"title":"[topic1_title]","description":"[topic1_description]","image":"[topic1_image]"},{"title":"[topic2_title]","description":"[topic2_description]","image":"[topic2_image]"}]}
               Instruction-> Return only json data no other words so it can be used by parsing and return empty on not able to extract or not available data.
            """, session_id=sessionid)
        # save agent response to database 
        message=data.data.output
        # save agent response to db
        agent_response = AgentResponse(session_id=sessionid, output=message)
        db.add(agent_response)
        db.commit()
  
        try:
            kit_data = json.loads(data.data.output)
            name=kit_data.get('name', '')
            pdf_path = f"static/Speaker_Kit_{name}__{int(time.time())}.pdf"
            create_speaker_kit_cover(
                pdf_path=pdf_path,
                bg_image_path="publicspeakerhero.jpeg",
                headshot_path1='' if kit_data.get('heashot1', '') == '' else "static" + kit_data['heashot1'].split("/static")[1],
                headshot_path='' if kit_data.get('headshots', '') == '' else "static" + kit_data['headshots'].split("/static")[1],
                speaker_name=kit_data.get('name', ''),
                tagline=kit_data.get('tagline', ''),
                tags=kit_data.get('subtagline', ''),
                blur_radius=15,
                about_text=kit_data.get('bio',             f"{name} is a visionary leader and acclaimed author, renowned for his "
            "transformative insights into modern leadership and technological innovation. "
            "With over two decades of experience, Jordan empowers organizations and individuals "
            "to navigate complex challenges and unlock their full potential in the digital age."),
                career_highlights=
                kit_data.get("career_highlights",
                [
                    "Authored best-selling book 'The AI Alchemist: ' ",
                    "Keynote speaker at over 100 international conferences on AI and leadership,",
                    "Led a groundbreaking initiative that resulted in a 30% efficiency ",
                    "Recognized as 'Top Innovator in Tech' by TechForward Magazine (2023)  ",
                    "Founded a highly successful startup focused on ethical AI solutions,  ",
                    "Delivered a highly-rated TEDx talk on 'The Future of Human-AI Collaboration .",
                ])
            )
            base_url = str(request.base_url)
            new_msg = ChatMessage(user="agent", message=f"{base_url}{pdf_path}", image=image, session_id=sessionid)
            db.add(new_msg)
            db.commit()
            db.close()
            return {"status": "ok", "message": f"{base_url}{pdf_path}"}
        except Exception as e:
            print("Error creating speaker kit:", e)
            return {"status": "error", "message": "Failed to create speaker kit."}
        
        # data=collector_agent.run("Extract data",session_id=sessionid)
        # print(data)
        # print(data)
        # res=json.loads(data)
        # print(data)
        # return {"status": "ok","message":data }
        # kit_data=request_speaker_kit(data.data.output)
        # print(kit_data)
        # pdf_path=f"static/Speaker_Kit_Cover_Two_Pages_Wide_Short{int(time.time())}.pdf"
        # create_speaker_kit_cover(
        #     pdf_path=pdf_path,
        #     bg_image_path="publicspeakerhero.jpeg", # Original unblurred image path
        #     headshot_path="static"+kit_data['images']['headshot']['url'].split("/static")[1],
        #     speaker_name=kit_data['name'],
        #     tagline=kit_data['tagline'],
        #     tags=kit_data['title'],
        #     blur_radius=15,
        #     about_text=(
        #         "Jordan Smith is a visionary leader and acclaimed author, renowned for his "
        #         "transformative insights into modern leadership and technological innovation. "
        #         "With over two decades of experience, Jordan empowers organizations and individuals "
        #         "to navigate complex challenges and unlock their full potential in the digital age."
        #     ),
        #     career_highlights=[
        #           "Authored best-selling book 'The AI Alchemist: ' ",
        #         "Keynote speaker at over 100 international conferences on AI and leadership,",
        #         "Led a groundbreaking initiative that resulted in a 30% efficiency ",
        #         "Recognized as 'Top Innovator in Tech' by TechForward Magazine (2023)  ",
        #         "Founded a highly successful startup focused on ethical AI solutions,  ",
        #         "Delivered a highly-rated TEDx talk on 'The Future of Human-AI Collaboration .",
        #     ]
        # )
        # base_url = str(request.base_url)  
        # new_msg = ChatMessage(user=username, message=f"{base_url}{pdf_path}", image=image,session_id=sessionid)
        # db.add(new_msg)
        # db.commit()
        # db.close() 
        # return {"status": "ok","message":"" f"{base_url}{pdf_path}" }


    db.close()
    # with open(MESSAGES_FILE, "r") as f:
    #     messages = json.load(f)
    # messages.append(data)
    # with open(MESSAGES_FILE, "w") as f:
    #     json.dump(messages[-50:], f)

    return {"status": "ok","message":message}
@app.get('/request-pdf',)
def get_mess(request:Request,db: Session = Depends(get_db)):
    sessionid = request.session.get("session")
    data=agent.run("provide me speaker kit of sesion",session_id=sessionid)
    print(data)
    kit_data=request_speaker_kit(data.data.output)
    print(kit_data)
    # return kit_data
    name=kit_data['name']
    pdf_path=f"static/Speaker_Kit_Cover_Two_Pages_Wide_Short{int(time.time())}.pdf"
    create_speaker_kit_cover(
        pdf_path=pdf_path,
        bg_image_path="publicspeakerhero.jpeg", # Original unblurred image path
        headshot_path=''if kit_data['images']['headshot']['url']=='' else "static"+kit_data['images']['headshot']['url'].split("/static")[1],
        speaker_name=kit_data['name'],
        tagline=kit_data['tagline'],
        tags=kit_data['title'],
        blur_radius=15,
        about_text=(
            f"{name} is a visionary leader and acclaimed author, renowned for his "
            "transformative insights into modern leadership and technological innovation. "
            "With over two decades of experience, Jordan empowers organizations and individuals "
            "to navigate complex challenges and unlock their full potential in the digital age."
        ),
        career_highlights=[
              "Authored best-selling book 'The AI Alchemist: ' ",
            "Keynote speaker at over 100 international conferences on AI and leadership,",
            "Led a groundbreaking initiative that resulted in a 30% efficiency ",
            "Recognized as 'Top Innovator in Tech' by TechForward Magazine (2023)  ",
            "Founded a highly successful startup focused on ethical AI solutions,  ",
            "Delivered a highly-rated TEDx talk on 'The Future of Human-AI Collaboration .",
        ]
    )
    return {"download_url": f"http://localhost:8000/{pdf_path}"}
    return (kit_data)
@app.get("/messages")
async def get_messages(request: Request,db: Session = Depends(get_db)):
    sessionid = request.session.get("session")
    messages = db.query(ChatMessage).filter(ChatMessage.session_id== sessionid).all()
    return messages
 
@app.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(UserSession).all()
    db.close()
    return [{"username": s.username, "sessionid": s.sessionid, "timestamp": s.timestamp.isoformat()} for s in sessions]
@app.get("/session/{session_id}")
async def get_session(session_id: str,request: Request,db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id== session_id).all()
    return messages

