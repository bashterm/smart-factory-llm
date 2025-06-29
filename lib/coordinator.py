class Coordinator:

  def __init__(self, procedures):
    self.procedures = procedures


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