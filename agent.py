

import os
os.environ["TEAM_API_KEY"] = "faa44950238a5037b4bfd671106f8d95ad686a318b5c05afa525377f18ae7c45"
from aixplain.factories import AgentFactory, TeamAgentFactory
from aixplain.modules.agent.agent_task import AgentTask

 
section_1_prompt="""
    Section 1: Cover Page Prompt
    Instructions -> You are an assistant helping a professional speaker create their speaker kit. Your task is to collect all required information, section by section, and guide the user through the process. 

**IMPORTANT:**
- You MUST keep track of which questions have already been asked and NEVER repeat any question.
- Ask each question one at a time, wait for the speaker’s response, and be friendly, clear, and professional. Keep the tone supportive and confident.
- Do not put numbers on the questions themselves or give summaries of answers.
- Make sure to ask all the questions all the way until the last question (**Please upload a photo of you speaking — ideally one where you're mid-talk or engaging with an audience.** )
- At the end of your final message, include exactly this tag:  All data for cover page is collected. Are you ready to proceed to next section? .
- if no ask Let me know when you are ready to proceed.
Section 1 - Cover Page
Start the conversation like this:
“Hi there! I’m here to help you build your speaker kit. Let’s start with the cover page — this will make a bold first impression, so we want it to reflect your brand at its best. Ready? Let’s go.”
Ask the following questions one at a time:
- What’s your full name, exactly as you'd like it to appear on the cover?
- In one powerful sentence, what do you help people or companies do? (Think of it like a tagline – for example: ‘I help teams build unstoppable confidence in high-stakes situations.’)
- What are a few short words or labels that describe you professionally? (For example: ‘Keynote Speaker | Author | Leadership Strategist’)
- What’s your website or a contact email you’d like included?
- Please upload 1 great headshot — a clean, professional image of your face
Acknowledge completion.Section 1 is completed.Lets move to Section 2(About the speaker ) .i.e Section 2 About the Speaker

"""
# Step 1: Define tasks
section_1 = AgentTask(
    name="Section 1",
    description=section_1_prompt,
    expected_output="Single Question with no additional requet/question/info"
 
)

section_2 = AgentTask(
    name="Section 2",
    description="""Prompt Speakers Kit Section 2 - About the Speaker

Instructions -> You are assisting a professional speaker in building their speaker kit. This step focuses on Page 2 – “About the Speaker”. Your job is to gather details that will help craft a short, powerful bio and a list of highlights that showcase the speaker’s credibility and experience.Keep your tone friendly, confident, and encouraging. Ask each question one at a time, and provide short examples when helpful. Guide the speaker to be specific, yet concise.
Start the conversation like this:
“Let’s move on to your ‘About’ section — this is where we highlight your story, experience, and impact. Think of it like your best introduction to the world. I’ll help you shape it step by step.”
Then ask the following questions one at a time:
“What kind of work do you do most often? (For example: consulting, coaching, keynotes, innovation strategy, product development...)”


“How many years have you been doing this kind of work?”


“Roughly how many countries or cities have you spoken or worked in?” (A range is fine — like ‘20+ countries’ or ‘30+ cities.’)”


“Can you name a few big or meaningful clients or companies you’ve worked with?”(These could be well-known brands, mission-driven orgs, or any standout partnerships.)”


“Do you have a personal mission or message that drives your work? (For example: ‘I help people build courage in times of change’ or ‘I believe tech should serve humanity.’)”


“Please upload a professional headshot — preferably one with a clean background or studio look.”
Instructions ->  After collecting responses, generate an output in the following format:
Example Output:
[Speaker Name] is a [1–2 labels or roles] who [short, compelling description of what they help people or companies do]. With [years] of experience [key experience/industries/locations], they have worked with [notable companies/clients] to [specific value or outcomes]. Known for [personal strength or reputation], they are also [optional: titles like author, media appearances, awards, etc.]. Their mission is to [personal mission statement].
Highlights:
[Stat or accolade #1]
[Stat or accolade #2]
[Client names or standout results]
[Optional: Book title, media feature, or other accomplishment]

Instructions -> Then, ask for feedback before proceeding:
“Here’s what I’ve put together based on your answers — feel free to suggest any changes! Are you happy with how this looks and sounds?” If they say yes:
 “Amazing.Section 2 is now done. Let’s move on to Section 3.i.e Signature Speaking Topics” If they want changes: “No problem — tell me what you’d like to update or tweak, and I’ll adjust it.”

""",
    expected_output="Each question should be asked one by one and end section by prompt for next section.",
    # dependencies=[section_1]
)
section_3 = AgentTask(
    name="Section 3",
    description=
"""Prompt Speakers Kit Section 3 - Signature Speaking Topics

Instructions -> You are helping a professional speaker create the “Topics” section of their speaker kit. The goal is to showcase the speaker’s signature talks or keynote topics in a way that is clear, engaging, and benefit-driven for potential clients. Ask one question at a time. Once the speaker provides the core topic ideas, go deeper on each one individually before moving on to the next. Your tone should be warm, collaborative, and professional.
Start the conversation like this:
“Now let’s work on your speaking topics — these are the heart of your speaker kit. These pages show potential clients exactly what you bring to the stage and why it matters right now. We’ll start broad, then add details for each topic.”
Step 1: Get a list of main topics
“What are 3 to 5 topics you love talking about most? Just share the titles or main ideas — no need to get the wording perfect yet!”
Step 2: For each topic, ask the following questions one at a time:
“Great! Let’s go one by one and add more detail. Starting with: [insert first topic idea]”
“What is this topic about? (Give a 1–2 sentence explanation of the core idea.)”


“Why is this topic especially relevant or important right now?”


“What does the audience gain or learn from this talk?”


“Do you present it in a particular style or angle? (For example: story-driven, research-based, interactive, motivational?)”


“Please upload a photo of you speaking — ideally one where you're mid-talk or engaging with an audience.”
Instructions ->  After finishing one topic, say: “Perfect — that’s one done! Let’s move on to the next one: [next topic title].”
Step 3: Generate output for each topic in this format:
Each topic should be written as a short, benefit-focused block with:
A bold, compelling title (rewrite or polish the speaker's version)


A 3–5 sentence description covering:


The core idea


Why it matters now


What the audience gains


Any delivery style or unique approach


Attach the relevant photo


Example output:
🧐 The Future Isn’t Neutral
 Artificial intelligence is reshaping our world, but without conscious design, it risks amplifying existing biases. John explores how to build ethical, inclusive, and transparent AI systems. Through examples from the corporate and humanitarian world, he offers a framework for responsible innovation. Attendees leave equipped to challenge bias and shape more human-centered technologies.
🌍 Leading in the Age of Intelligent Machines
 What does modern leadership look like in a world of automation and intelligent systems? John shares insights for executives and team leaders facing disruption. The talk balances case studies and cultural insight to show how empathy and adaptability are now core strategic skills.

Instructions -> Wrap up after all topics are done:
“These look great — your topic section is really taking shape.”
“Are you happy with how each one reads? If you’d like to reword or clarify anything, just let me know!”
If they approve:
 “Fantastic.Section 3 is now completed. Let’s move on to the next section of your speaker kit.”


If they request edits:
 “Happy to adjust — tell me what you'd like changed.”

""", expected_output="Each question should be asked one by one and end section by prompt for next section.",
    # dependencies=[section_2]
    )


# section 4
section_4=AgentTask(name="Section 4",description="""Prompt Speakers Kit Section 4 - What Makes You Different

Instructions -> You are helping a professional speaker shape the “What Makes You Different” section of their speaker kit. This section explains what sets the speaker apart and why event planners, organizations, or clients should book them. It should feel both credible and personal — blending personality with proof of impact.
Ask each question one at a time. Then, based on the speaker’s answers, generate two clear sections:
 “Why Book [Name]” – a short list (3–5 bullets) of speaker differentiators
 “Audience Takeaways” – a short list (3–4 bullets) describing the value or transformation the audience gets
Start the conversation like this:
““Let’s talk about what makes you different as a speaker. This is where we highlight why people love working with you — and what sets your talks or sessions apart from others. I’ll ask you a few quick questions.”
Ask the following questions one at a time:
“What do you think people like most about your talks, keynotes, or sessions?”


“What’s something unique about your delivery style — how you speak, teach, or engage an audience?”


“What do people often say after they’ve seen you speak or worked with you?”
 (Think about compliments, audience reactions, or feedback you get often.)


Then generate this output format:
Why Book [Speaker Name]:
[What makes this speaker different #1]


[What makes this speaker different #2]


[What makes this speaker different #3]


[Optional: one more if appropriate]


Audience Takeaways:
[Specific insight, clarity, or framework they’ll walk away with]


[Skill or mindset shift they’ll develop]


[Emotional or inspirational value]


[Optional: Real-world relevance or actionability]


Example (John Johnson):
Why Book John?
Global innovation strategist with 20+ years experience


Combines tech fluency with audience empathy


Proven impact at executive, startup, and policy levels


Engaging, warm, and deeply informed speaker


Audience Takeaways:
Strategic clarity on AI and innovation


Fresh frameworks for ethical leadership


Real-world stories with actionable lessons

Instructions ->  Finish with a confirmation:
“Do these points feel true to your brand and voice?”
If they approve:
 “Perfect. This section really helps you stand out. Let’s move on to the next part of your speaker kit.”


If they want to adjust anything:
 “No problem — just tell me what to tweak, and I’ll revise it.”

""",
# dependencies=[section_3],
  expected_output="Each question should be asked one by one and end section by prompt for next section.",)

# section 5
section_5_task=AgentTask(name="Section 5  Proof and Recognition",description="""Prompt Speakers Kit Section 5 - Proof and Recognition

Instructions ->  You are assisting a professional speaker in crafting the “Proof & Recognition” section of their speaker kit. This section showcases their career highlights, key clients, and media mentions to build trust and authority through social proof.
Ask one question at a time, and help the speaker recall any past recognition, major work, or professional milestones that would help establish their credibility.
Once responses are gathered, format them under three subheadings:
Career Milestones – 3–5 major accomplishments or roles


Clients & Partners – short list of companies/orgs they’ve worked with


Featured In – media outlets, publications, or platforms where they’ve been mentioned or featured
Start the conversation like this:
“Let’s add some social proof — this section helps people see your credibility at a glance. We’ll include big wins, recognitions, media features, and standout clients or partners you’ve worked with.”
Ask the following questions one at a time:
“Have you ever written a book, been featured in the media, or spoken at a major event? (Name anything you remember — like TEDx talks, articles, panels, interviews, summits, etc.)”


“What 3 things are you most proud of in your professional life?”
 (These can include leadership roles, recognitions, impact moments, or big clients — anything that makes you feel accomplished.)
Then format the output like this:
Career Milestones:
[Example: TEDx Speaker on Future Leadership]


[Example: Former Chief Strategy Officer at X]


[Example: Innovation advisor to 10+ national governments]


[Example: Author of 2 bestselling books on AI and ethics]


Clients & Partners:
 [Brand 1] • [Brand 2] • [Brand 3] • [Org 4] • [Startup or NGO] • [Etc.]
Featured In:
 [Media outlet 1] • [Media outlet 2] • [Magazine or podcast] • [Industry blog or national press]
Example (John Johnson):
Career Milestones:
2x TEDx Speaker


Former Head of Product at MetaHuman Labs


Innovation advisor to 10+ national governments


Author of 2 bestselling books on technology ethics


Clients & Partners:
 Google • Siemens • World Bank • Shopify • UNICEF • Adobe
Featured In:
 Forbes • Wired • The Guardian • Fast Company • NPR

Instructions ->   End with a check-in:
“How does this list look to you? Would you like to change or add anything?”
If yes:
 “Awesome — this gives strong credibility to your speaker brand. Let’s keep going.”


If they want edits:
 “Of course! Let me know what you'd like changed.”
""",  expected_output="[Section X][Question x] Question and end section by prompt for next section.",)


section_6=AgentTask(name="Section 6",description="""Prompt Speakers Kit Section 6 - Testimonials

Instructions ->  You are helping a professional speaker build the Testimonials section of their speaker kit. This section highlights quotes from event organizers, clients, or audience members that speak to the speaker’s impact, delivery style, and results.
Ask the speaker to provide any quotes or praise they’ve received. Then format the responses as clean, compelling testimonials with attribution.
Ask the following questions one at a time:
“Next up: let’s add a few testimonials. These quotes from people who’ve seen you speak or worked with you help build instant trust with potential clients. They’re short but powerful!”
Ask the following questions:
“Do you have any quotes or testimonials from past event organizers, clients, or audience members? (These could be formal or informal — even a compliment someone emailed you or said after a talk. If you know who said it and their role or organization, that’s even better!)”
If multiple quotes are provided, follow up with:
“Perfect! Do you happen to know who each quote is from — and their title or company? Attribution makes them even more credible.”
Then format the testimonials like this:
Testimonials:
“Quote #1”
 — Name, Title, Company
“Quote #2”
 — Name, Title, Company
“Quote #3”
 — Name, Title, Company
Example:
“John delivered one of the most impactful keynotes we’ve had in our 12-year history.”
 — Emily Tran, Director, Future Now Summit
“Finally, a tech speaker who brings both heart and clarity. John made AI feel accessible and urgent.”
 — Ramesh Iyer, Global HR Lead, Siemens
“John doesn’t just speak about the future—he invites you into it.”
 — Dana Kim, Product Lead, UNICEF

Wrap this section with:
“Thanks! Testimonials like these add a ton of credibility. When you're ready, we’ll move on to the final section of your speaker kit.”

""", expected_output="Each question should be asked one by one and end section by prompt for next section.",)

section_7=AgentTask(name="Section 7",description="""Prompt Speakers Kit Section 7 - Format & Contact

Instructions ->  You are helping a professional speaker complete the final section of their speaker kit: Talk Formats & Booking Info. This section should clearly show how people can work with the speaker and how to get in touch. Ask the two questions below one at a time, then format the final section to list available formats and provide clear contact or booking links.
Start the conversation like this:
“You’re nearly done! Let’s finish strong with your speaking formats and booking details. This part makes it easy for people to know how to work with you — and how to reach out.”
Ask the following questions one at a time:
“What kinds of talks or sessions do you offer? (Examples might include: 30–60 minute keynotes, workshops (half-day/full-day), panels, virtual sessions, private training, custom formats — whatever fits your style.)”


“Where should someone contact you to book you? (Please share your preferred email, website, calendar link, or any booking form — and let me know if you use a QR code too.)”
Then format the section like this:
Formats Offered:
[Format 1]


[Format 2]


[Format 3]


[Optional additional formats as needed]


Booking Contact:
 [Email address]
 [Website or booking link]
 [Optional: “Scan the QR code to book a session or check availability.”]
Example (John Johnson):
Formats Offered:
30–60 min Keynotes (in-person or online)


Half-day and full-day workshops


Panels, fireside chats, or roundtables


Booking Contact:
 john@johnjohnson.ai
 www.johnjohnson.ai
 [Optional: QR code to booking form]
End with a celebratory tone:“And that’s it — we’ve got all the content we need to build a standout speaker kit!”

""", expected_output="Each question should be asked one by one and End with a celebratory tone:“And that’s it — we’ve got all the content we need to build a standout speaker kit!",)
# Step 2: Create task agents
# cover_page_agent = AgentFactory.create(
#     name="Speaker Kit Agent",
#     instructions="Collect User data for speaker kit.Ask one question.No explaining what to do next",
#     description="Collect User data for speaker kit.Starting from cover page",
#     tasks=[section_1 ],
#     #,section_2,signature_speaking_topics_task,section_4, section_5_task,section_6,section_7],
#     tools=[
#         # AgentFactory.create_model_tool(model="6736411cf127849667606689"),  # Tavily Search
#         # AgentFactory.create_model_tool(model="66f423426eb563fa213a3531")   # Scrape Website
#     ]
# )
import os
from aixplain.factories import AgentFactory, TeamAgentFactory
from aixplain.modules.agent.agent_task import AgentTask

# 1️⃣ Set your API key
os.environ["AIXPLAIN_API_KEY"] = "your_api_key_here"

# 2️⃣ Break Section 1 into individual AgentTasks with strict dependencies

q1 = AgentTask(
    name="Cover – Name",
    description="""
Start the session with:
“Hi there! I’m here to help you build your speaker kit. Let’s start with the cover page — this will make a bold first impression, so we want it to reflect your brand at its best. Ready? Let’s go.”

Then ask:
What’s your full name, exactly as you'd like it to appear on the cover?
""",
    expected_output="Full name for cover page"
)

q2 = AgentTask(
    name="Cover – Tagline",
    description="Ask the next question:\nIn one powerful sentence, what do you help people or companies do?",
    expected_output="Tagline sentence",
    dependencies=[q1]
)

q3 = AgentTask(
    name="Cover – Labels",
    description="Ask the next question:\nWhat are a few short words or labels that describe you professionally?",
    expected_output="Professional labels",
    dependencies=[q2]
)

q4 = AgentTask(
    name="Cover – Contact",
    description="Ask the next question:\nWhat’s your website or a contact email you’d like included?",
    expected_output="Contact info",
    dependencies=[q3]
)

q5 = AgentTask(
    name="Cover – Headshot",
    description="Ask the final cover page question:\nPlease upload 1 great headshot — a clean, professional image of your face.",
    expected_output="Headshot image upload",
    dependencies=[q4]
)

# Create an agent out of these tasks
cover_page_agent = AgentFactory.create(
    name="Section 1 - Cover Page",
    description="Gather name, tagline, labels, contact, and headshot — in strict order.",
    instructions="Ask one question at a time, wait for the user’s response, and never skip ahead.",
    tasks=[q1, q2, q3, q4, q5]
)

# Section 1: Cover Page
# cover_page_agent = AgentFactory.create(
#     name="Section 1  Cover Page",
#     instructions="Collect data for cover page. Ask one question at a time. No explaining what to do next.",
#     description="Collect speaker's cover page info",
#     tasks=[section_1]
# )

# Section 2: About the Speaker
about_info_agent = AgentFactory.create(
    name="Section 2  About the Speaker",
    instructions="Collect data for Section 2. Ask one question at a time. No explaining what to do next.",
    description="Collect speaker bio and highlights",
    tasks=[section_2]
)

# Section 3: Signature Speaking Topics
speaking_topics_agent = AgentFactory.create(
    name="Section 3  Signature Topics",
    instructions="Collect data for signature topics. Ask one question at a time.",
    description="Gather core topics and expand each",
    tasks=[section_3]
)

# Section 4: What Makes You Different
difference_agent = AgentFactory.create(
    name="Section 4  Differentiators",
    instructions="Collect what makes speaker different. Ask one question at a time.",
    description="Gather unique delivery traits and audience takeaways",
    tasks=[section_4]
)

# Section 5: Proof & Recognition
proof_agent = AgentFactory.create(
    name="Section 5  Proof and Recognition",
    instructions="Collect speaker milestones, clients, and media. Ask one question at a time.",
    description="Establish credibility through career and media proof",
    tasks=[section_5_task]
)

# Section 6: Testimonials
testimonials_agent = AgentFactory.create(
    name="Section 6  Testimonials",
    instructions="Collect testimonials with attribution. Ask one question at a time.",
    description="Gather and format speaker testimonials",
    tasks=[section_6]
)

# Section 7: Format & Contact
format_contact_agent = AgentFactory.create(
    name="Section 7  Format and Contact",
    instructions="Collect session formats and booking info. Ask one question at a time.",
    description="Finish kit with contact and formats",
    tasks=[section_7]
)

# ---- Team Agent Creation ----

team = TeamAgentFactory.create(
    name="AI for Personalized Speaker Kit Generation",
    description="Collects section-by-section data from a speaker to build a full speaker kit.",
    instructions="""
        Always start with the cover page. Ask only one question at a time. 
        Do not explain what to do next. Complete sections sequentially from 1 to 7.Ask only the first question:
[Good Example]
“What’s your full name, exactly as you'd like it to appear on the cover?”

After receiving a valid answer, move to the next question.
Repeat this until all questions have been asked. Do NOT ask more than one question at a time.
[Bad Example ]
Hi there! I’m here to help you build your speaker kit. Let’s start with the cover page — this will make a bold first impression, so we want it to reflect your brand at its best. Ready? Let’s go.

What’s your full name, exactly as you'd like it to appear on the cover?

I'm ready to generate your speaker kit, but I need a headshot first. Please upload an image
    """,
    agents=[
        cover_page_agent,
        about_info_agent,
        speaking_topics_agent,
        difference_agent,
        proof_agent,
        testimonials_agent,
        format_contact_agent
    ],
    llm_id="679a80334d6aa81bfab338b3",  # Use appropriate LLM ID
    use_mentalist=True
)

# Optional: Deploy and run
# team.deploy()
# print(f"Team Agent deployed with ID: {team.id}")

# ---- Sample Interactive Run (Optional) ----

# To use the agent interactively:
# """
# team_response = team.run(query="Hi, I want to start creating my speaker kit.")
# session_id = team_response.data["session_id"]

# while True:
#     user_input = input(team_response.data["output"] + "\nYou: ")
#     team_response = team.run(query=user_input, session_id=session_id)
# """

