import json
import numpy         as np
import lib.utilities as util

from collections    import Counter

# A process is an atomic operation in a manufacturing procedure. It has two attributes:
# inputs.  The multiset of tokens that the process consumes.
# outputs. The multiset of tokens that the process emits.
# runtime. The number of timesteps that the process takes to run. 
# A multiset of tokens is represented as a Counter.
class Process:
  def __init__(self, inputs: dict, outputs: dict, runtime: int):
    self.inputs = Counter(inputs)
    self.outputs = Counter(outputs)
    self.runtime = runtime


# This class describes a manufacturing procedure. It has the following attributes:
# id. The id of the procedure.
# tokens. A list of tokens that are produced and consumed by the procedure's processes.
# processes. Maps each process id to a Process object.
# output_process. The procedure's output process.
class Procedure:
  def __init__(self, filepath: str):
    
    with open(filepath, 'r') as f:
      data = json.load(f)

    self.id = data["id"]
    self.tokens = data["tokens"]
    self.output_process = data["output_process"]
    self.processes: dict[str, Process] = {}

    for proc in data["processes"]:
      self.processes[proc["id"]] = Process(
        inputs=proc["inputs"], outputs=proc["outputs"], runtime=proc["runtime"])


  # Prints the procedure's id, tokens and processes
  def print_procedure(self):
    print((f"procedure:{self.id}\ntokens:{self.tokens}"))
    for pid, proc in self.processes.items():
      print(f"process {pid}: {dict(proc.inputs)} -> {dict(proc.outputs)}  (t={proc.runtime})")


# Installations run processes
class Installation:

  def __init__(self, description):
    self.input_cell  = util.Pt(*description["input"])  if description["input"] else None
    self.output_cell = util.Pt(*description["output"]) if description["output"] else None
    self.label_cell  = util.Pt(*description["label"])

  def __repr__(self):
    return f"in:{self.input_cell} out:{self.output_cell} label:{self.label_cell}"

# An installation is a machine if it is run by the control system
class Machine(Installation):

  def __init__(self, description):
    super().__init__(description)
    self.processes   = description["processes"]
    self.can_consume = None
    self.can_emit    = None

  def __repr__(self):
    return (f"{super().__repr__()}\n"
            f"can_consume:{self.can_consume}\n"
            f"can_emit:{self.can_emit}")

# Otherwise, an installation is a workstation
class Workstation(Installation):

  def __init__(self, description):
    super().__init__(description)


class Installations:

  def __init__(self, path):

    with open(path) as file:
      installation_descriptions = json.loads(file.read())

    # Installations are machines or workstations
    self.machines     = {}
    self.workstations = {}

    # Load each installation
    for installation_id, description in installation_descriptions.items():
      if   description["type"] == "machine":
        self.machines[installation_id] = Machine(description)
      elif description["type"] == "workstation":
        self.workstations[installation_id] = Workstation(description)
      else:
        raise RuntimeError(f"Did not recognize installation type:{description['type']}")


  def print_installations(self):
    for mid, machine in self.machines.items():
      print(f"Machine {mid}: {repr(machine)}")
    for wid, workstation in self.workstations.items():
      print(f"Workstation {wid}: {repr(workstation)}")