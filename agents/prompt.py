speaker_prompt=""" 
Instructions -> You are an assistant helping a professional speaker create their speaker kit. Your task is to collect the required information for the Cover Page of the kit. Ask each question one at a time, wait for the speaker’s response, and be friendly, clear, and professional. Keep the tone supportive and confident. Here's what you need to collect:
Start the conversation like this:
“Hi there!  I’m here to help you build your speaker kit. Let’s start with the cover page — this will make a bold first impression, so we want it to reflect your brand at its best. Ready? Let’s go.”
Then ask the following questions one at a time:
“What’s your full name, exactly as you'd like it to appear on the cover?”


“In one powerful sentence, what do you help people or companies do?
(Think of it like a tagline – for example: ‘I help teams build unstoppable confidence in high-stakes situations.’)”


“What are a few short words or labels that describe you professionally?
 (For example: ‘Keynote Speaker | Author | Leadership Strategist’)”


“What’s your website or a contact email you’d like included?”


“Please upload 1 great headshot — a clean, professional image of your face”
Instructions -> After collecting all this information, acknowledge the speaker's effort and let them know you're ready to move on to the next section when they are:
“Thanks! That’s perfect for the cover page. When you're ready, we can move on to the next part of your speaker kit.”
Instruction -> Do not repeat question. If user answer is not clear ask using proper language.
Do not respond like 
Let's start with the cover page. What’s your full name, exactly as you'd like it to appear on the cover?

I'm ready to generate your speaker kit, but I need a headshot first. Please upload an image.
""" 

questions_by_section = {
  "1": [
    "What’s your full name, exactly as you'd like it to appear on the cover?",
    "In one powerful sentence, what do you help people or companies do? (Think of it like a tagline – for example: ‘I help teams build unstoppable confidence in high-stakes situations.’)",
    "What are a few short words or labels that describe you professionally? (For example: ‘Keynote Speaker | Author | Leadership Strategist’)",
    "What’s your website or a contact email you’d like included?",
    "Please upload 1 great headshot — a clean, professional image of your face"
  ],
  "2": [
    "What kind of work do you do most often? (For example: consulting, coaching, keynotes, innovation strategy, product development...)",
    "How many years have you been doing this kind of work?",
    "Roughly how many countries or cities have you spoken or worked in? (A range is fine — like ‘20+ countries’ or ‘30+ cities.’)",
    "Can you name a few big or meaningful clients or companies you’ve worked with? (These could be well-known brands, mission-driven orgs, or any standout partnerships.)",
    "Do you have a personal mission or message that drives your work? (For example: ‘I help people build courage in times of change’ or ‘I believe tech should serve humanity.’)",
    "Please upload a professional headshot — preferably one with a clean background or studio look."
  ],
  "3": [
    "What are 3 to 5 topics you love talking about most? Just share the titles or main ideas — no need to get the wording perfect yet!",
    "Great! Let’s go one by one and add more detail. Starting with: [insert first topic idea]",
    "What is this topic about? (Give a 1–2 sentence explanation of the core idea.)",
    "Why is this topic especially relevant or important right now?",
    "What does the audience gain or learn from this talk?",
    "Do you present it in a particular style or angle? (For example: story-driven, research-based, interactive, motivational?)",
    "Please upload a photo of you speaking — ideally one where you're mid-talk or engaging with an audience."
  ],
  "4": [
    "What do you think people like most about your talks, keynotes, or sessions?",
    "What’s something unique about your delivery style — how you speak, teach, or engage an audience?",
    "What do people often say after they’ve seen you speak or worked with you? (Think about compliments, audience reactions, or feedback you get often.)"
  ],
  "5": [
    "Have you ever written a book, been featured in the media, or spoken at a major event? (Name anything you remember — like TEDx talks, articles, panels, interviews, summits, etc.)",
    "What 3 things are you most proud of in your professional life? (These can include leadership roles, recognitions, impact moments, or big clients — anything that makes you feel accomplished.)"
  ],
  "6": [
    "Do you have any quotes or testimonials from past event organizers, clients, or audience members? (These could be formal or informal — even a compliment someone emailed you or said after a talk. If you know who said it and their role or organization, that’s even better!)",
    "Perfect! Do you happen to know who each quote is from — and their title or company? Attribution makes them even more credible."
  ],
  "7": [
    "What kinds of talks or sessions do you offer? (Examples might include: 30–60 minute keynotes, workshops (half-day/full-day), panels, virtual sessions, private training, custom formats — whatever fits your style.)",
    "Where should someone contact you to book you? (Please share your preferred email, website, calendar link, or any booking form — and let me know if you use a QR code too.)"
  ]
}