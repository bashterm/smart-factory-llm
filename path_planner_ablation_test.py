import json
import lib.utilities          as     util

from lib.map                  import Map
from lib.scenario             import Installations
from lib.simple_path_planner  import SimplePathPlanner
from lib.workstation          import Workstation
from lib.visualizer           import Visualizer


# (1) Load Config
config_path     = "config/action_figure.json"
llm_config_path = "config/llm_config.json"

with open(config_path) as file:
  config = json.loads(file.read())

with open(llm_config_path) as file:
  llm_config = json.loads(file.read())


# (2) Load installations and the factory map
installations = Installations(config["machines_path"])
installations.print_installations()

factory_map = Map(config["map_path"], installations)
factory_map.visualize()
vis = Visualizer(factory_map, installations, 1)


# (3) Add conditions to the factory map
conditions = [("There is an oil spill in the center of the factory. Use roads which hug the "
               "factory outskirts."), "The road (6,7)->(6,1) is blocked by a broken down robot."]

for condition in conditions: factory_map.add_condition(condition)


# (4) Initialize path planners
simple_path_planner = SimplePathPlanner(path_planner_model = "gpt-4o")


# (5) Run path planners

simple_path_planner.plan_junction_path(factory_map = factory_map, 
                                       start_cell  = util.Pt(0,5), 
                                       goal_cell   = util.Pt(1,1))
