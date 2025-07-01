import json

from lib.coordinator          import Coordinator
from lib.map                  import Map
from lib.scenario             import Installations, Procedure
from lib.simple_interpreter   import SimpleInterpreter
from lib.workstation          import Workstation
from lib.visualizer           import Visualizer

class SmartFactorySystem:

  def __init__(self, config_path, llm_config_path):

    # (1) Load Config
    with open(config_path) as file:
      config     = json.loads(file.read())

    with open(llm_config_path) as file:
      llm_config = json.loads(file.read())

    # (2) Load procedures
    self.procedures    = [Procedure(filepath) for filepath in config["procedure_paths"]]

    # (3) Load 

    # (2) Load installations and factory map
    self.installations = Installations(config["installations_path"])
    self.installations.print_installations()

    self.factory_map   = Map(config["factory_map_path"], self.installations)
    self.factory_map.visualize()

    # (3) Load visualizer
    self.visualizer    = Visualizer(self.factory_map, self.installations, num_agents=1)

    # (4) Load procedures and coordinator
    
    self.coordinator   = Coordinator(procedures, config["to_execute_path"], self.installations)

  def update(self):

    # 1) Pull information interpreters

    # 2) Update workstation state

    # 3) Run scheduler. The scheduler makes sure that each machine has a task assigned to it and
    #    that each agent has a task assigned to. 

    # 4) Agents run path planner if they need to

    # 5) System updates


if __name__ == "__main__":
  smart_factory = SmartFactorySystem(config_path     = "config/simple_test_II.json",
                                     llm_config_path = "config/llm_config.json")
