import json
import lib.path_planner   as path_planner
import lib.process_status as process_status
import lib.run_factory    as run_factory
import lib.scenario       as scenario
import lib.utilities      as util
import lib.visualizer     as visualizer
import lib.workstation_interpreter as workstation_interpreter
import sys
import time

from collections import Counter

from lib.map                import Map
from lib.coordinator        import Coordinator
# from lib.build_traffic_plan import BuildTrafficPlan

# interpreter = workstation_interpreter.InterpreterGamma(["gpt-4o", "gpt-4o", "gpt-4o", "gpt-4o"])
# interpreter.main()
# sys.exit()

# (1) Load Config
config_path     = "config/action_figure.json"
llm_config_path = "config/llm_config.json"

with open(config_path) as file:
  config = json.loads(file.read())

with open(llm_config_path) as file:
  llm_config = json.loads(file.read())


# (2) Load Factory and Procedures
procedures  = [scenario.Procedure(filepath) for filepath in config["procedure_paths"]]
# [procedure.print_procedure() for procedure in procedures]
coordinator = Coordinator(procedures)
coordinator.print_all_tokens()
coordinator.print_all_processes()

intepreter_examples_filepath = config["interpreter_example_path"]
interpreter = workstation_interpreter.Interpreter(
  ["gpt-4o"] * 4, coordinator, intepreter_examples_filepath, llm_config["maximum_context_length"])

interpreter.main()

sys.exit()

installations = scenario.Installations(config["machines_path"])
installations.print_installations()

factory_map = Map(config["map_path"], installations)
# factory_map.visualize()
vis = visualizer.Visualizer(factory_map, installations, 1)

agents = [run_factory.Agent(1, util.Pt(0,2))]
agents[0].add_cargo(Counter({"plank":2, "chassis":1}))
vis.generate_state(agents)


condition1 = ("There is an oil spill in the center of the factory. "
              "Please use roads which hug the factory outskirts.")

condition2 = ("The road (6,7)->(6,1) is blocked by a broken down robot.")

factory_map.add_condition(condition1)
factory_map.add_condition(condition2)

pplanner = path_planner.PathPlanner(
  proposer_models   = ["gpt-4o", "gpt-4o"], 
  aggregator_models = ["gpt-4o", "gpt-4o"])


pplanner.plan_junction_path(factory_map, util.Pt(0,5), util.Pt(1,1))

sys.exit()



# (2) Load Scenario
procedure1 = scenario.Procedure("tests/simple_test/procedures/simple_procedure1.json")
procedure2 = scenario.Procedure("tests/simple_test/procedures/simple_procedure2.json")

machines   = scenario.Machines(config["machines_path"], procedure)
machines.print_machines()

m = Map(config["map_path"], machines)

procedures = {
  procedure1.id: procedure1,
  procedure2.id: procedure2
}

for procedure in procedures.values():
  procedure.print_procedure()

# Specify how many times to run each procedure
to_run = Counter({
  procedure1.id: 5,
  procedure2.id: 3
})

status = process_status.ProcessStatus(procedures, to_run)
status.print_process_status()

interpreter = workstation_interpreter.Interpreter(["gpt-4o", "gpt-4o", "gpt-4o", "gpt-4o"])
interpreter.main()

# interpreter = workstation_interpreter.Interpreter(status, ["gpt-4o","gpt-4o","gpt-4o","gpt-4o"], 0.75)
# interpreter.main()


sys.exit()



machines   = scenario.Machines(config["machines_path"], procedure)
machines.print_machines()

m = Map(config["map_path"], machines)
# m.visualize()

num_epochs           = 2
timesteps_per_epoch  = 6
agent_limit          = 1000


plan = PlanGenerator(procedure, machines, m, num_epochs, timesteps_per_epoch, agent_limit)

plan.model.optimize()
plan.print_objective()

plan.plot_plan(procedure, machines, m, T=0)
# plan.plot_plan(procedure, machines, m, T=1)
# plan.plot_plan(procedure, machines, m, T=2)

st_t = time.time()
builder = BuildTrafficPlan(procedure, machines, m, plan, num_epochs, timesteps_per_epoch)
input(f"{time.time()-st_t} build:{builder.total_agents}")


# Alg 2
def plan_num_epochs(delta, time_limit, num_epochs, gamma):
  best_sol = 0
  best_time = None
  num_iters = 0
  ts_per_epoch = max([len(r.path) for r in m.roads]) + 1 + delta
  start_t = time.time()
  while (time.time() - start_t < time_limit*1000) and num_iters < gamma:
    plan = PlanGenerator(procedure, machines, m, num_epochs, ts_per_epoch)
    plan.model.optimize()
    sol = plan.get_objective()
    if sol > best_sol:
      best_sol = sol
      best_time = ts_per_epoch
    ts_per_epoch += delta
    num_iters += 1
  print(f"Best sol {best_sol} with time {best_time}")

# plan_num_epochs(1, 30, 3, 25)


