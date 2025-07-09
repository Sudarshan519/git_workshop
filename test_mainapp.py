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
        
    if message.__contains__("a professional headshot") or message.__contains__("Please upload a professional headshot"):
        data = agent.run(
            """extract data from the session in json format like 
               {"name":"[Name]" ,"email":"[Email]","website":"[website]","headshots":"[image_link]","tagline":"[tagline]","subtagline":"[subtagline]","bio":"[bio],"career_highlights":["[highlight1]","[highlight2]","[highlight3]"],"topics":[{"title":"[topic1_title]","description":"[topic1_description]","image":"[topic1_image]"},{"title":"[topic2_title]","description":"[topic2_description]","image":"[topic2_image]"}]}
               Instruction-> Return only json data no other words so it can be used by parsing
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
            pdf_path = f"static/Speaker_Kit_Cover_Two_Pages_Wide_Short{int(time.time())}.pdf"
            create_speaker_kit_cover(
                pdf_path=pdf_path,
                bg_image_path="publicspeakerhero.jpeg",
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
            new_msg = ChatMessage(user=username, message=f"{base_url}{pdf_path}", image=image, session_id=sessionid)
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
@app.get("/pdf")
async def get_messages(request: Request,db: Session = Depends(get_db)):
    sessionid = request.session.get("session")
    messages = db.query(ChatMessage).filter(ChatMessage.session_id== sessionid).order_by(desc(ChatMessage.timestamp)).first()
    response=agent.run("Use collected data to crete a speaker kit in html.Do not provide any instruction or any text provide only html for speaker kit " ,session_id=sessionid)
    # print(messages.message)
    return HTMLResponse(
      
        response.data.output
        +
        
        
        """ <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">    <style>    :root {
      --primary: #1a73e8;
      --bg: #f5f7fa;
      --text: #333;
      --section-bg: #ffffff;
      --muted: #777;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
    }

    header {
      background: var(--section-bg);
      padding: 60px 20px;
      text-align: center;
      box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }

    header h1 {
      font-size: 2.8rem;
      font-weight: 700;
    }

    header p.tagline {
      font-size: 1.2rem;
      margin: 10px 0;
      color: var(--primary);
    }

    header p.titles {
      font-size: 1rem;
      color: var(--muted);
    }

    header .contact {
      margin-top: 10px;
      font-size: 0.95rem;
    }

    header .hero {
      margin-top: 30px;
      max-width: 700px;
      margin-left: auto;
      margin-right: auto;
      border-radius: 12px;
      overflow: hidden;
    }

    section {
      background: var(--section-bg);
      margin: 40px auto;
      padding: 50px 20px;
      max-width: 960px;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    h2 {
      font-size: 2rem;
      margin-bottom: 20px;
      border-bottom: 2px solid #eee;
      padding-bottom: 10px;
    }

    h3 {
      font-size: 1.2rem;
      margin-top: 30px;
      margin-bottom: 10px;
      color: var(--primary);
    }

    ul {
      margin-left: 20px;
      margin-bottom: 20px;
    }

    .topic {
      margin-top: 30px;
    }

    .topic img {
      width: 100%;
      border-radius: 8px;
      margin-top: 10px;
    }

    .testimonial {
      background: #f0f3f6;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 20px;
    }

    .testimonial .author {
      margin-top: 10px;
      font-style: italic;
      color: var(--muted);
      text-align: right;
    }

    .contact-block {
      text-align: center;
      margin-top: 20px;
    }

    .contact-block a {
      color: var(--primary);
      font-weight: 600;
    }

    footer {
      text-align: center;
      font-size: 0.9rem;
      color: #999;
      padding: 40px 20px 20px;
    }

    img {
      width: 100%;
      max-width: 100%;
      display: block;
    }

    @media (max-width: 768px) {
      header h1 {
        font-size: 2rem;
      }

      section {
        padding: 30px 15px;
      }

      h2 {
        font-size: 1.5rem;
      }
    } @page {
        margin: 0; /* Try to remove default browser margins */
      }

      body {
        margin: 1cm; /* Add your own custom margins */
      }

      /* Optional: hide elements not needed in print */
      .no-print {
        display: none;
      }
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
        }
        .page {
            page-break-after: always;
            padding: 20px;
        }
        .cover-page {
            text-align: center;
        }
        .cover-page img {
            max-width: 100%;
            height: auto;
        }
        .bio {
            margin-bottom: 20px;
        }
        .highlights {
            list-style-type: none;
            padding: 0;
        }
        .talk {
            margin-bottom: 30px;
        }
        .talk img {
            max-width: 100%;
            height: auto;
        }
        .testimonials {
            margin-bottom: 20px;
        }
        .testimonial {
            margin-bottom: 10px;
        }
        .booking-info {
            margin-bottom: 20px;
        }
        .export-button {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 15px 32px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
        }
    </style>"""+"    <script>window.print()</script>")

@app.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(UserSession).all()
    db.close()
    return [{"username": s.username, "sessionid": s.sessionid, "timestamp": s.timestamp.isoformat()} for s in sessions]
@app.get("/session/{session_id}")
async def get_session(session_id: str,request: Request,db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id== session_id).all()
    return messages

