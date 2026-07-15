from crewai import Crew, Process
from src.agents.shortform_agents import create_shortform_agents
from src.tasks.shortform_tasks import create_shortform_tasks

def run_shortform_crew(topic):
    researcher, writer, director, video_critic = create_shortform_agents()
    research_task, write_task, direct_task, critique_task = create_shortform_tasks(
        researcher, writer, director, video_critic, topic
    )
    
    crew = Crew(
        agents=[researcher, writer, director, video_critic],
        tasks=[research_task, write_task, direct_task, critique_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew.kickoff()