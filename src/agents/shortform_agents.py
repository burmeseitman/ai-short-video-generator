import os
import yaml
from crewai import Agent
from src.config_llm import get_llm, get_writer_llm

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_path = os.path.join(root_dir, 'config', 'agents.yaml')

with open(config_path, 'r', encoding='utf-8') as f:
    agents_config = yaml.safe_load(f)

def create_shortform_agents():
    llm = get_llm()
    writer_llm = get_writer_llm()

    researcher = Agent(
        config=agents_config['researcher'],
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    writer = Agent(
        config=agents_config['writer'],
        verbose=True,
        allow_delegation=False,
        llm=writer_llm
    )

    director = Agent(
        config=agents_config['director'],
        verbose=True,
        allow_delegation=False,
        llm=writer_llm
    )

    return researcher, writer, director