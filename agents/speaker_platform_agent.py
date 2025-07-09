import os
os.environ["TEAM_API_KEY"] = "faa44950238a5037b4bfd671106f8d95ad686a318b5c05afa525377f18ae7c45"
from aixplain.factories import AgentFactory
from textwrap import dedent
from agents.prompt import speaker_prompt
# Create a model tool
# model_tool = AgentFactory.create_model_tool(
#     model="679a80334d6aa81bfab338b3", # Grok 2
#     description="A language model for text summarization." # Optional
# )
agent = AgentFactory.create(
    name="Speaker kit creator agent",
    # tools=[
    #     model_tool
    # ],
    description="An interactive speaker agent that help user create speaker kit.Ask one question at a time.Move to next section only when user is ready.",
    llm_id="679a80334d6aa81bfab338b3", # Grok 2
    instructions=dedent(speaker_prompt)  # GPT 4o
)

# collector_agent = AgentFactory.create(
#     name="CollectorAgent",
#     description="Validates and structures user information",
#     instructions=dedent("""
#     You receive raw user responses and must:
#     1. Validate each field:
#        - Email must be valid format
#        - Age must be positive integer
#        - Name must be at least 2 words
#     2. Transform into structured JSON
#     3. Handle validation errors by requesting corrections
#     4. Pass validated data to ExportAgent
    
#     Validation Rules:
#     - name: Required, min 2 words
#     - email: Valid email format
#     - age: Positive integer 13-120
#     - location: Non-empty string
#     """),
#     tools=[],  # Could add validation tools here
    
# )

# print(agent.id)
# agent=AgentFactory.get(
#     '6865ed6161f3437545d8a6b3'
# )
# agent=AgentFactory.get("6865437f68a95b7daa729660")
# print(agent.id)
# agent.deploy()
# all_existing_agents = AgentFactory.list()
# for existing_agent in all_existing_agents:
#     print(str(existing_agent.get("name")))
    # if hasattr(existing_agent, 'name') and existing_agent.name == "Speaker kit creator agent":
    #     print(existing_agent['name'])
