import json

from lib.agent                import Agent
from lib.coordinator          import Coordinator
from lib.installations        import build_installations, print_installations
from lib.map                  import Map
from lib.procedures           import Procedures
from lib.simple_interpreter   import SimpleInterpreter
from lib.visualizer           import Visualizer

class SmartFactorySystem:

  def __init__(self, config_path, llm_config_path, num_agents):

    # (1) Load Config
    with open(config_path) as file:
      config     = json.loads(file.read())

    with open(llm_config_path) as file:
      llm_config = json.loads(file.read())

    # (2) Load procedures
    self.procedures   = Procedures(config["procedure_paths"], config["required_runs_path"])

    # (3) Load machines, workstations and factory map
    self.machines, self.workstations = build_installations(config["installations_path"])
    print_installations(self.machines, self.workstations)

    self.factory_map  = Map(config["factory_map_path"])
    # self.factory_map.visualize()

    # (4) Load coordinator
    self.coordinator  = Coordinator(self.procedures)
    self.coordinator.print_unassigned_processes()
    
    # (5) Load agents
    self.agents       = {agent_id:Agent(agent_id) for agent_id in range(num_agents)}

    # (6) Load visualizer
    self.visualizer   = Visualizer(self.factory_map, self.machines, self.workstations, 
                                   len(self.agents))

    # (7) Load interpreters
    self.interpreters = (
      {workstation_id : SimpleInterpreter(
                          intepreter_llm_model   = "gpt-4o", 
                          question_llm_model     = "gpt-4o", 
                          procedures             = self.procedures,
                          examples_filepath      = config["interpreter_example_path"], 
                          maximum_context_length = llm_config["maximum_context_length"],
                          workstation_id         = workstation_id,
                          workstation            = workstation)
      for workstation_id, workstation in self.workstations.items()})
      

  def update(self):
 
    # 1) Pull information from interpreters
    for interpreter in self.interpreters.values():  # Make this async?
      interpreter.get_update(self.coordinator)

    # 2) Run scheduler. The scheduler makes sure that each machine has a task assigned to it and
    #    that each agent has a task assigned to. 

    # 4) Agents run path planner if they need to

    # 5) System updates


if __name__ == "__main__":
  smart_factory = SmartFactorySystem(config_path     = "config/simple_test_II.json",
                                     llm_config_path = "config/llm_config.json",
                                     num_agents      = 4)
  smart_factory.update()
