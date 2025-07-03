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

  def __eq__(self, process):
    if not isinstance(process, Process):
      return NotImplemented
    
    return (
          self.runtime == process.runtime
      and self.inputs  == process.inputs 
      and self.outputs == process.outputs
    )

  def to_str_with_pid(self, pid):
    return f"process {pid}: {dict(self.inputs)} -> {dict(self.outputs)}  (t={self.runtime})"


# This class describes a manufacturing procedure. It has the following attributes:
# id. The id of the procedure.
# tokens. A list of tokens that are produced and consumed by the procedure's processes.
# processes. Maps each process id to a Process object.
# output_process. The procedure's output process.
class Procedure:
  def __init__(self, filepath):
    
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
    for pid, process in self.processes.items():
      print(process.to_str_with_pid(pid))


# This class describes a set of manufacturing procedures. It allows you to look up:
# a) information about individual manufacturing procedures
# b) the set of all manufacturing procedures
# c) the set of all tokens
# d) the number of times each procedure should be executed
class Procedures:

  def __init__(self, procedure_filepaths, required_runs_filepath):

    # Get the set of all manufacturing procedures
    self.procedures    = [Procedure(filepath) for filepath in procedure_filepaths]

    # Get a map from each procedure id to the number of times that it has to be run
    with open(required_runs_filepath) as file:
      self.required_runs = json.loads(file.read())


  # Gets the set of all processes in the procedures
  def get_all_processes(self):

    processes = {}

    for procedure in self.procedures:
      for pid, process in procedure.processes.items():

        # If processes already contains a process with pid, make sure that the two processes
        # are identical.
        if pid in processes:
          assert processes[pid] == process, (
            f"Two processes:\n"
            f"{process.to_str_with_pid(pid)}\n"
            f"{processes[pid].to_str_with_pid(pid)}\n"
            f"share the same pid but are not identical")

        # Otherwise, add the process to the dict
        else:
          processes[pid] = process

    return processes


  # Prints the procedures' processes
  def print_all_processes(self):
    processes = self.get_all_processes()
    for pid, process in processes.items():
      print(process.to_str_with_pid(pid))


  # Gets the set of all tokens in the procedures
  def get_all_tokens(self):
    return set().union(*[set(procedure.tokens) for procedure in self.procedures])


  # Prints the procedures' tokens
  def print_all_tokens(self):
    print(self.get_all_tokens())