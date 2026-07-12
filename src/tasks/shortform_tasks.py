import os
import yaml
from crewai import Task

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_path = os.path.join(root_dir, 'config', 'tasks.yaml')

with open(config_path, 'r', encoding='utf-8') as f:
    tasks_config = yaml.safe_load(f)

def create_shortform_tasks(researcher, writer, director, topic):
    # Inject topic into every task so all agents stay grounded to the specific subject
    research_desc   = tasks_config['research_task']['description'].format(topic=topic)
    research_output = tasks_config['research_task']['expected_output'].format(topic=topic)

    write_desc      = tasks_config['write_task']['description'].format(topic=topic)
    write_output    = tasks_config['write_task']['expected_output'].format(topic=topic)

    direct_desc     = tasks_config['direct_task']['description'].format(topic=topic)
    direct_output   = tasks_config['direct_task']['expected_output'].format(topic=topic)

    research_task = Task(
        description=research_desc,
        expected_output=research_output,
        agent=researcher
    )

    write_task = Task(
        description=write_desc,
        expected_output=write_output,
        agent=writer,
        context=[research_task]
    )

    direct_task = Task(
        description=direct_desc,
        expected_output=direct_output,
        agent=director,
        context=[research_task, write_task]
    )

    return research_task, write_task, direct_task