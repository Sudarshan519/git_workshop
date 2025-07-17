from slides.google_slide import create_speaker_kit_slides


slides_url = create_speaker_kit_slides({
                "bg_image_path": "publicspeakerhero.jpeg",
                "headshot_path": 'https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D',
                "name":"Sudarshan Shrestha",
                "title":"sdkslj",
                "tags": "sdlkfj",
                "bio": "dksfjlskjf",
                "career_highlights": [
                    "Authored best-selling book 'The AI Alchemist: ' ",
                    "Keynote speaker at over 100 international conferences on AI and leadership,",
                    "Led a groundbreaking initiative that resulted in a 30% efficiency ",
                    "Recognized as 'Top Innovator in Tech' by TechForward Magazine (2023)  ",
                    "Founded a highly successful startup focused on ethical AI solutions,  ",
                    "Delivered a highly-rated TEDx talk on 'The Future of Human-AI Collaboration .",
                ],
                "topics": [
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
                ]
            })
print("Slides created at:", slides_url)
