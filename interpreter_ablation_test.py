import json

from lib.coordinator             import Coordinator
from lib.scenario                import Procedure
from lib.simple_interpreter      import SimpleInterpreter
from lib.workstation             import Workstation
from lib.workstation_interpreter import Interpreter


# (1) Load Config
config_path     = "config/action_figure.json"
llm_config_path = "config/llm_config.json"

with open(config_path) as file:
  config = json.loads(file.read())

with open(llm_config_path) as file:
  llm_config = json.loads(file.read())


# (2) Load procedures, workstations and coordinator
procedures   = [Procedure(filepath) for filepath in config["procedure_paths"]]
workstations = {"w_test":Workstation()}
coordinator  = Coordinator(procedures, config["to_execute_path"], workstations)


# (3) Initialize interpreters
simple_interpreter = SimpleInterpreter(
  workstation_id         = "w_test",
  intepreter_llm_model   = "gpt-4o", 
  question_llm_model     = "gpt-4o", 
  coordinator            = coordinator, 
  examples_filepath      = config["interpreter_example_path"], 
  maximum_context_length = llm_config["maximum_context_length"])


# (4) Run interpreters
# simple_interpreter.main()
