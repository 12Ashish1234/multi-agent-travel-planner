from planner_agent.agent import root_agent

if __name__ == "__main__":
    response = root_agent.run("Can you plan a 3-day trip to Paris?")
    print(response)
