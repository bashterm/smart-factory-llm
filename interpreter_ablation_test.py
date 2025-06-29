import json

from lib.coordinator             import Coordinator
from lib.scenario                import Procedure
from lib.simple_interpreter      import SimpleInterpreter
from lib.workstation_interpreter import Interpreter


# (1) Load Config
config_path     = "config/action_figure.json"
llm_config_path = "config/llm_config.json"

with open(config_path) as file:
  config = json.loads(file.read())

with open(llm_config_path) as file:
  llm_config = json.loads(file.read())


# (2) Load Procedures and Coordinator
procedures  = [Procedure(filepath) for filepath in config["procedure_paths"]]
coordinator = Coordinator(procedures)


# (3) Initialize interpreters
simple_interpreter = SimpleInterpreter(
  intepreter_llm_model   = "gpt-4o", 
  question_llm_model     = "gpt-4o", 
  coordinator            = coordinator, 
  examples_filepath      = config["interpreter_example_path"], 
  maximum_context_length = llm_config["maximum_context_length"])


# (4) Run interpreters
simple_interpreter.main()
