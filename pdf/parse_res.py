import json

# Your provided JSON string
json_string = "{\"name\": \"Jane Doe\", \"title\": \"Data Scientist\", \"bio\": \"Jane is a data scientist with 10 years of experience. She is passionate about using data to solve real-world problems.  She has a PhD in Statistics from Stanford University.\", \"images\": {\"backgroundImage\": {\"url\": \"https://example.com/background.jpg\", \"caption\": \"Jane Doe at a conference\", \"description\": \"Image of Jane Doe speaking at a conference\"}, \"headshot\": {\"url\": \"https://example.com/headshot.jpg\", \"caption\": \"Jane Doe headshot\", \"description\": \"Headshot of Jane Doe\"}}, \"topics\": [{\"title\": \"Data Science\", \"image\": {\"url\": \"https://example.com/data_science.jpg\", \"caption\": \"Data Science\"}}, {\"title\": \"Machine Learning\", \"image\": {\"url\": \"https://example.com/machine_learning.jpg\", \"caption\": \"Machine Learning\"}}, {\"title\": \"Artificial Intelligence\", \"image\": {\"url\": \"https://example.com/ai.jpg\", \"caption\": \"Artificial Intelligence\"}}], \"talkFormats\": [{\"type\": \"Keynote\", \"duration\": \"60 minutes\"}, {\"type\": \"Workshop\", \"duration\": \"90 minutes\"}, {\"type\": \"Panel Discussion\", \"duration\": \"45 minutes\"}], \"pastEngagements\": [{\"title\": \"Data Science Conference\", \"year\": 2022}, {\"title\": \"Machine Learning Summit\", \"year\": 2023}], \"testimonials\": [{\"quote\": \"Jane is an excellent speaker. She is very knowledgeable and engaging.\", \"author\": \"John Smith\"}, {\"quote\": \"I learned a lot from Jane's presentation.\", \"author\": \"Alice Johnson\"}], \"whyBook\": [\"Jane is a highly sought-after speaker.\", \"She is an expert in her field.\", \"She is engaging and informative.\"], \"contact\": {\"email\": \"jane.doe@example.com\", \"phone\": \"123-456-7890\", \"website\": \"https://example.com\", \"linkedin\": \"https://www.linkedin.com/in/janedoe\"}}"

# Convert the JSON string to a Python dictionary
data = json.loads(json_string)
abc={"name": "Sudarshan Shrestha", "email": "sudarshan@gmail.com", "website": "", "headshots": "http://localhost:8000/static/uploads/9cf6134306194a1e8c4c75336a8934e0.jpg", "headshot1": "https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D", "tagline": "I help teams build unstoppable confidence in high-stakes situations", "subtagline": "Keynote Speaker | Author | Leadership Strategist", "bio": "Sudarshan Shrestha is a seasoned professional with 10 years of experience in product development, having worked in over 30 cities. He has collaborated with notable clients like AI Industry Rockstar and Hotei. Driven by the belief that 'tech should serve humanity,' Sudarshan combines expertise with a mission to make a meaningful impact through his work.", "career_highlights": ["10 years of experience in product development", "Worked in over 30 cities globally", "Collaborated with AI Industry Rockstar", "Partnered with Hotei", "Specializes in AI Agentic Framework Development", "Delivers research-based talks on AI and tech"], "topics": [{"title": "AI Agentic Framework Development", "description": "Build agents to do a specific task", "image": "https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D"}]}
print(json.dumps(abc))
# You now have a Python dictionary 'data' that represents your JSON
print("Python Dictionary (data):")
print(data)

# You can access elements like this:
print("\nAccessing specific elements:")
print(f"Name: {data['name']}")
print(f"Title: {data['title']}")
print(f"First topic: {data['topics'][0]['title']}")
print(f"Contact email: {data['contact']['email']}")

# If you want to convert the Python dictionary back to a pretty-printed JSON string:
pretty_json_string = json.dumps(data, indent=2)
print("\nPretty-printed JSON string:")
print(pretty_json_string)