import os
os.environ["TEAM_API_KEY"] = "faa44950238a5037b4bfd671106f8d95ad686a318b5c05afa525377f18ae7c45"
from aixplain.factories import AgentFactory
from speaker_platform import speaker_prompt
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
    description="An interactive speaker agent that help user create speaker kit.",
    llm_id="679a80334d6aa81bfab338b3", # Grok 2
    instructions=speaker_prompt # GPT 4o
)
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
