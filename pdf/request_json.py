import requests
import json

reqUrl = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyApKT7PSA0Dg79soh1J80Wu8QkiU7rud5g"

headersList = {
 "Accept": "*/*",
 "User-Agent": "Thunder Client (https://www.thunderclient.com)",
 "Content-Type": "application/json" 
}
def request_speaker_kit(data:str):
    payload = json.dumps({
        "contents": [
        {
            "parts":[
            { "text": f"Generate a speaker kit using the data {data}" }
            ]
        }
        ],
        "systemInstruction": {
            "role": "user",
            "parts": [
                {
                    "text": "Provide the response using schema of available information.No sample images should be added.If no image in information provide empty string"
                }
            ]
        },
        "generationConfig": {
            "temperature": 0.15,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
        
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "tagline": {
                            "type": "STRING"
                        },
                        "name": {
                            "type": "STRING"
                        },
                        "title": {
                            "type": "STRING"
                        },
                        "bio": {
                            "type": "STRING"
                        },
  "career_highlights": {
    "type": "ARRAY",
    "items": {
      "type": "OBJECT",
      "properties": {
        "title": {
          "type": "STRING",
          "description": "A short, clear title for the achievement"
        }}}},
                        "images": {
                            "type": "OBJECT",
                            "properties": {
                                "backgroundImage": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "url": {
                                            "type": "STRING"
                                        },
                                        "caption": {
                                            "type": "STRING"
                                        },
                                        "description": {
                                            "type": "STRING"
                                        }
                                    },
                                    "propertyOrdering": [
                                        "url",
                                        "caption",
                                        "description"
                                    ]
                                },
                                "headshot": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "url": {
                                            "type": "STRING"
                                        },
                                        "caption": {
                                            "type": "STRING"
                                        },
                                        "description": {
                                            "type": "STRING"
                                        }
                                    },
                                    "propertyOrdering": [
                                        "url",
                                        "caption",
                                        "description"
                                    ]
                                }
                            },
                            "propertyOrdering": [
                                "backgroundImage",
                                "headshot"
                            ]
                        },
                        "topics": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "title": {
                                        "type": "STRING"
                                    },
                                    "image": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "url": {
                                                "type": "STRING"
                                            },
                                            "caption": {
                                                "type": "STRING"
                                            }
                                        },
                                        "propertyOrdering": [
                                            "url",
                                            "caption"
                                        ]
                                    }
                                },
                                "propertyOrdering": [
                                    "title",
                                    "image"
                                ]
                            }
                        },
                        "talkFormats": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "type": {
                                        "type": "STRING"
                                    },
                                    "duration": {
                                        "type": "STRING"
                                    }
                                },
                                "propertyOrdering": [
                                    "type",
                                    "duration"
                                ]
                            }
                        },
                        "pastEngagements": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "title": {
                                        "type": "STRING"
                                    },
                                    "year": {
                                        "type": "NUMBER"
                                    }
                                },
                                "propertyOrdering": [
                                    "title",
                                    "year"
                                ]
                            }
                        },
                        "testimonials": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "quote": {
                                        "type": "STRING"
                                    },
                                    "author": {
                                        "type": "STRING"
                                    }
                                },
                                "propertyOrdering": [
                                    "quote",
                                    "author"
                                ]
                            }
                        },
                        "whyBook": {
                            "type": "ARRAY",
                            "items": {
                                "type": "STRING"
                            }
                        },
                        "contact": {
                            "type": "OBJECT",
                            "properties": {
                                "email": {
                                    "type": "STRING"
                                },
                                "phone": {
                                    "type": "STRING"
                                },
                                "website": {
                                    "type": "STRING"
                                },
                                "linkedin": {
                                    "type": "STRING"
                                }
                            },
                            "propertyOrdering": [
                                "email",
                                "phone",
                                "website",
                                "linkedin"
                            ]
                        }
                    },
                    "propertyOrdering": [
                        "name",
                        "title",
                        "bio",
                        "images",
                        "topics",
                        "talkFormats",
                        "pastEngagements",
                        "testimonials",
                        "whyBook",
                        "contact"
                    ]
                }
        
        }
    })

    response = requests.request("POST", reqUrl, data=payload,  headers=headersList)

    json_string=(response.json()['candidates'][0]['content']['parts'][0]['text'])


 
    # Convert the JSON string to a Python dictionary
    data = json.loads(json_string)
    return data