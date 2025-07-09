from  app import create_speaker_kit_cover


kit_data={"name":"Sudarshan Shrestha","email":"","website":"sudarshan.vercel.com","headshots":"http://localhost:8000/static/uploads/76a1bb8068914f9f86ef3092c0562c37.png","heashot1":"http://localhost:8000/static/uploads/2a3c267115aa47f792316e0952217a56.png","tagline":"I help team build up ai agents and prompts","subtagline":"Keynote Speaker | Author | Leadership Strategist","bio":"Sudarshan Shrestha is a Keynote Speaker | Author | Leadership Strategist who helps teams build up AI agents and prompts. With over 10 years of experience in product development, he has worked in 50+ countries and spoken in more than 3 languages. He has worked with Industry Rockstar, 1 2 3, AI district agents, hotei, and mission-driven organizations to advance their goals. Known for his dedication to technology serving humanity, his mission is to ensure tech serves humanity.","career_highlights":["10+ years in product development","50+ countries visited and spoken in more than 3 languages","Worked with Industry Rockstar, 1 2 3, AI district agents, hotei, and mission-driven organizations"],"topics":[{"title":"AI Development","description":"Despite the lack of funding during the AI Winter, the early 90s showed some impressive strides forward in AI research, including the introduction of the first AI system that could beat a reigning world champion chess player. This era also saw early examples of AI agents in research settings, as well as the introduction of AI into everyday life via innovations such as the first Roomba and the first commercially-available speech recognition software on Windows computers. The surge in interest was followed by a surge in funding for research, which allowed even more progress to be made. Notable dates include: 1997: Deep Blue beat the world chess champion, Gary Kasparov, in a highly-publicized match, becoming the first program to beat a human chess champion. 1997: Windows released a speech recognition software. 2000: Professor Cynthia Breazeal developed the first robot that could simulate human emotions with its face, called Kismet. 2002: The first Roomba was released.","image":""},{"title":"Agent Development, chatbot and other ai related works","description":"","image":""}]}
name=kit_data.get('name', 'Sudarshan Shrestha')
create_speaker_kit_cover(
                pdf_path="Speaker_Kit_Cover_Two_Pages_Wide_sShort.pdf",
                bg_image_path="publicspeakerhero.jpeg",
                headshot_path1='' if kit_data.get('headshot1', '') == '' else "static" + kit_data['headshot1'].split("/static")[1],
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