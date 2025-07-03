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
    for pid, process in self.processes.items():
      print(process.to_str_with_pid(pid))


