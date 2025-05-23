from collections import Counter
import json

# Tracks the status of the processes that the factory has to run.
# ATTRIBUTE 1: unscheduled. The multiset of processes which haven't been scheduled.
# ATTRIBUTE 2: scheduled_or_running. The multiset of processes which are scheduled or running.
# ATTRIBUTE 3: finished. The multiset of processes which are finished.
class ProcessStatus:
  def __init__(self, procedures, to_run):
    self.unscheduled = Counter()
    self.scheduled_or_running = Counter()
    self.finished = Counter()

    # Initialize unscheduled with each process repeated per run count
    for pid, count in to_run.items():
      procedure = procedures[pid]
      for pid in procedure.processes:
        self.unscheduled[pid] += count

  # Schedules a set of unscheduled processes
  def schedule_processes(self, processes):
    if not processes <= self.unscheduled:
      raise RuntimeError(f"Cannot schedule processes {processes}: not all are unscheduled")

    for proc_id, count in processes.items():
      self.unscheduled[proc_id] -= count
      self.scheduled_or_running[proc_id] += count

  # Finishes a set of scheduled or running processes
  def finish_processes(self, processes):
    if not processes <= self.scheduled_or_running:
      raise RuntimeError(f"Cannot finish processes {processes}: not all are scheduled or running")

    for proc_id, count in processes.items():
      self.scheduled_or_running[proc_id] -= count
      self.finished[proc_id] += count

  # Return a copy of unscheduled to prevent external mutation
  def get_unscheduled(self):
    return self.unscheduled.copy()

  def print_process_status(self):
    print(f"unscheduled: {dict(self.unscheduled)}")
    print(f"scheduled_or_running: {dict(self.scheduled_or_running)}")
    print(f"finished: {dict(self.finished)}")
