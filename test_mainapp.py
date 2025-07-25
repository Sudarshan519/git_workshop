import json
from typing import Optional
import markdown
from requests import Session
from fastapi import FastAPI, Request, Form, UploadFile, File,Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
# from git_workflow.pdf.test import kit_data
from ideogram_request import get_background_image
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
import ast

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware



import logging
# Add this at the top of your file for basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# === Setup ===
app = FastAPI()
app.add_middleware(SessionMiddleware,    
                    secret_key="your-secret-key",
                    same_site="none",       # <-- Required for cross-site cookie
                    https_only=True  )
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
    # Add this new column to store the Google Slides Presentation ID
    google_slide_id = Column(String, nullable=True)     # Added 2025/07/23 


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
        
        try:
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            image_url = f"/static/uploads/{filename}"
            logger.info(f"Successfully saved file to: {filepath}")
            
            # Construct agent_input here, now that image_url is determined
            agent_input = f"{original_message}\n{base_url}{image_url}" if original_message else f"{base_url}{image_url}"

        except Exception as e: # <--- START OF EXCEPT BLOCK
            logger.error(f"Error saving file {filename} to {filepath}: {e}")
            # If saving fails, image_url remains None, which is important for the next step
            # You might want to return an error response here if file upload is critical
            # return JSONResponse(status_code=500, content={"detail": f"Failed to upload image: {e}"})
            agent_input = message # Use only message if image upload fails
            image_url = None # Ensure image_url is None if save failed
    else:
        agent_input = message # If no file, agent_input is just the message
    
    db.add(ChatMessage(user=username, message=original_message, image=image_url, session_id=sessionid))
    db.commit()
    
    agent_response = team.run( agent_input, session_id=sessionid)
    # print(agent_response.__dict__)
    agent_message_content = agent_response.data.output
    print(agent_message_content)


    # Check if speaker kit generation is triggered (adjust this condition as per your agent's output)
    # Check if speaker kit generation is triggered (adjust this condition as per your agent's output)
    if "FINAL_STAGE:complete" in agent_message_content:
        try:
            jsondata = agent_message_content.replace("```json","").replace("```",'')
            kit_data = json.loads(jsondata)

            # Define a default or configurable background image URL
            # IMPORTANT: Replace this with an actual public URL to an image you want to use.
            # This image will be used as the background for your Google Slides.
            background_image_url="https://firebasestorage.googleapis.com/v0/b/chat-app-c5vy3d.appspot.com/o/tmp17_mnre7.png?alt=media&token=a7255094-e0a0-4105-95de-49f89f4e1ea9" # Example, replace with YOUR image URL

            # Call create_speaker_kit_slides with the correct arguments: kit_data and bg_image_path
            # As per your google_slide.py, it always creates a NEW presentation.
            # If you want to UPDATE an existing one, create_speaker_kit_slides needs to be modified.
            presentation_id, slides_url = create_speaker_kit_slides(
                kit_data=kit_data,
                bg_image_path=background_image_url
            )

            # Retrieve the UserSession for the current session (ensure db_user_session is already defined/fetched earlier in /send)
            # This makes sure we're updating the session object tied to the current DB transaction
            user_session_to_update = db.query(UserSession).filter(UserSession.sessionid == sessionid).first()

            if user_session_to_update:
                user_session_to_update.google_slide_id = presentation_id
                db.commit()
                db.refresh(user_session_to_update)
                logger.info(f"Updated UserSession with Google Slide ID: {presentation_id}")
            else:
                logger.warning(f"UserSession not found for session_id: {sessionid}. Could not save google_slide_id.")

            # Store the agent's response with the kit_data
            agent_response_db = AgentResponse(session_id=sessionid, output=json.dumps(kit_data))
            db.add(agent_response_db)
            db.commit()

            # Prepare the message for the user, including the slide URL
            final_agent_message = f"\n\nCongratulations! Your speaker kit is ready. [View/Download Slides]({slides_url})"
            db.add(ChatMessage(user="agent", message=final_agent_message, session_id=sessionid))
            db.commit()
            
            # Return a response that includes the slides_url for your frontend
            return {"status": "ok", "message": markdown.markdown(final_agent_message), "slides_url": slides_url}
        
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding agent response JSON for slides: {e}")
            final_agent_message = "Sorry, I couldn't process the speaker kit data. There was an issue with the format."
            db.add(ChatMessage(user="agent", message=final_agent_message, session_id=sessionid))
            db.commit()
            return {"status": "error", "message": markdown.markdown(final_agent_message)}

        except Exception as e:
            logger.error(f"Error generating slides: {e}")
            final_agent_message = f"Sorry, an error occurred while generating slides: {e}"
            db.add(ChatMessage(user="agent", message=final_agent_message, session_id=sessionid))
            db.commit()
            return {"status":"error", "message": markdown.markdown(final_agent_message)}


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
    agent_response=db.query(AgentResponse).filter(AgentResponse.session_id==session_id).all()
    if not agent_response:
    # return messages
    # sessionid = request.session.get("session")
        data=team.run("""extract data from the session in json format like 
                {
                    "name": "[Name]",
                    "email": "[Email]",
                    "website": "[Website]",
                    "headshots": "[image_link_section_1]",
                    "heashot1": "[image_link_section2]",
                    "tagline": "[Tagline]",
                    "subtagline": "[Subtagline]",
                    "bio": "[About speaker]",
                    "career_highlights": ["[highlight1]", "[highlight2]", "[highlight3]"],
                    "topics": [
                        {"title": "[topic1_title]", "description": "[topic1_description]", "image": "[topic1_image]"},
                        {"title": "[topic2_title]", "description": "[topic2_description]", "image": "[topic2_image]"}
                    ],
                    "why_book": ["[reason1]", "[reason2]", "[reason3]"],
                    "audience_takeaways": ["[takeaway1]", "[takeaway2]", "[takeaway3]"],
                    "career_milestones": ["[milestone1]", "[milestone2]", "[milestone3]"],
                    "clients_partners": ["[client1]", "[client2]", "[client3]"],
                    "featured_in": ["[media1]", "[media2]", "[media3]"],
                    "testimonials": [
                        {"quote": "[testimonial1]", "author": "[author1]", "role": "[role1]"},
                        {"quote": "[testimonial2]", "author": "[author2]", "role": "[role2]"}
                    ],
                    "formats_offered": ["[format1]", "[format2]", "[format3]"],
                    "booking_contact": {
                        "email": "[booking email]",
                        "website": "[booking website]",
                        "form": "[booking form link]",
                        "phone": "[phone number]",
                        "qr_code": "[qr code image or link]"
                    }
                }
                Instruction-> Return only json data no other words so it can be used by parsing and return empty on not able to extract or not available data.Generate at least 6 carrer highlights,and bio should not be empty should be generate from about.Json should be able to load using json.loads([output]).Avoid adding lines
            """,session_id=session_id)
        # print(f"This is the raw data: {data}")
        kit_datas=data.data.output
        # Fix broken newlines inside the JSON string
        fixed_json = kit_datas 
        # print(f"This is data: {kit_datas}")
        # print("")
        # # with open("abc.json",'w')as f:
        # #     f.write(kit_datas)
        # print(f"Fixed Data: {fixed_json}")
        # print("")
        agent_response = AgentResponse(session_id=session_id, output=kit_datas)
        db.add(agent_response)
        db.commit()
        jsondata=(data.data.output)
    else:
        kit_datas = agent_response[-1].output
        jsondata = kit_datas

    # kit_data=request_speaker_kit(data.data.output)
    # jsondata=(data.data.output)
    # print("jsondata:", jsondata)
    # print(json.loads(jsondata))
    # Step 1: Convert to dict
    # print(data.data.output['bio'])
    # Step 3: Convert back to dict via JSON
    # json_string = json.dumps(jsondata) 
    # kit_data = ast.literal_eval(jsondata)
    # print(f"This is the data in JSON: {kit_data}")
    # print(jsondata)
    # --- START OF MODIFICATIONS ---
    try:
        # Use json.loads for parsing JSON, it's safer and standard
        kit_data = ast.literal_eval(kit_datas) 
    except (ValueError, SyntaxError) as e:
        logger.error(f"Error evaluating agent response as Python literal in /request-pdf: {e}. Raw data that caused error: {kit_datas}")
        return JSONResponse(status_code=500, content={"message": "Failed to process speaker kit data from agent: Invalid data format (not valid Python literal)."})
    
    # Add bio only if it is missing or empty (keep your existing logic)
    if not kit_data.get("bio"):
        kit_data["bio"] = "This is a default bio describing the speaker's background and expertise."

    career_highlights = kit_data.get("career_highlights", [])
    while len(career_highlights) < 6:
        career_highlights.append("")
    kit_data["career_highlights"] = career_highlights # Update kit_data with potentially padded highlights

    # Define the background image URL
    # IMPORTANT: REPLACE THIS URL with your actual desired background image URL.
    # background_path = get_background_image()
    # print("Background image URL:", background_path)
    # background_image_url = "https://firebasestorage.googleapis.com/v0/b/chat-app-c5vy3d.appspot.com/o/tmp17_mnre7.png?alt=media&token=a7255094-e0a0-4105-95de-49f89f4e1ea9" # YOUR IMAGE URL!

    # Call create_speaker_kit_slides (without existing_presentation_id, always creates new)
    try:
        prompt_data = json.dumps(kit_data)  # or a string that summarizes kit_data as prompt
        background_image_url = get_background_image(prompt_data, aspect_ratio="16x9")
        # print("Background image URL from ideogram:", background_image_url)


        from slides.google_slide import process_speaker_kit_images
        kit_data = process_speaker_kit_images(kit_data)
        print("Processed kit_data:", kit_data)

        # Call create_speaker_kit_slides (without existing_presentation_id, always creates new)
        presentation_id, slides_url = create_speaker_kit_slides(
            kit_data=kit_data,
            bg_image_path=background_image_url
        )
    except Exception as e:
        logger.error(f"Error creating Google Slides: {e}")
        return JSONResponse(status_code=500, content={"message": f"Failed to generate slides: {e}"})

    # Find the user session to update the google_slide_id
    user_session_to_update = db.query(UserSession).filter(UserSession.agent_session_id == session_id).first()

    if user_session_to_update:
        user_session_to_update.google_slide_id = presentation_id
        db.commit()
        db.refresh(user_session_to_update)
        logger.info(f"Updated UserSession with Google Slide ID: {presentation_id} in /request-pdf.")
    else:
        logger.warning(f"UserSession not found for session_id: {session_id}. Could not save google_slide_id in /request-pdf.")

    # Update the ChatMessage to correctly state "View Slides" instead of "Download PDF"
    db.add(ChatMessage(user="agent", message=f"\n\nCongratulations! Your speaker kit slides are ready! [View Slides]({slides_url})", session_id=session_id))
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
    return {"download_url": f"http://localhost:8000/{pdf_path}", "slides_url": slides_url}
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

@app.get("/ideogram")
def get_ideogram_image(request:Request):
    return get_background_image("""{'name': 'Sudarshan Shrestha', 'email': 'sudarshan@gmail.com', 'website': '', 'headshots': 'http://localhost:8000/static/uploads/9cf6134306194a1e8c4c75336a8934e0.jpg', 'headshot1': 'https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D', 'tagline': 'I help teams build unstoppable confidence in high-stakes situations', 'subtagline': 'Keynote Speaker | Author | Leadership Strategist', 'bio': "Sudarshan Shrestha is a seasoned professional with 10 years of experience in product development, having worked in over 30 cities. He has collaborated with notable clients like AI Industry Rockstar and Hotei. Driven by the belief that 'tech should serve humanity,' Sudarshan combines expertise with a mission to make a meaningful impact through his work.", 'career_highlights': ['10 years of experience in product development', 'Worked in over 30 cities globally', 'Collaborated with AI Industry Rockstar', 'Partnered with Hotei', 'Specializes in AI Agentic Framework Development', 'Delivers research-based talks on AI and tech'], 'topics': [{'title': 'AI Agentic Framework Development', 'description': 'Build agents to do a specific task', 'image': 'https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D'}]}""")