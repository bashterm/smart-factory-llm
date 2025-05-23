from enum import Enum
from collections import Counter
from typing import Optional
import scenario

# An Enum which lists the possible update types
class UpdateType(Enum):
  Schedule = 1   # The workstation is scheduling processes
  Run      = 2   # The workstation is running scheduled processes
  Finish   = 3   # The workstation has finished running processes

# Formally represents an update from a workstation.
# update_type: UpdateType. The type of update.
# processes: Counter. The relevant proceses
class Update:
  def __init__(self, update_type: UpdateType, processes: Counter[scenario.Process, int]):
    self.update_type = type
    self.processes   = processes


class Workstation:
  def __init__(self):
    # multisets of processes
    self.scheduled: Counter[scenario.Process, int] = Counter()
    self.running:   Counter[scenario.Process, int] = Counter()
    # buffer of tokens
    self.buffer:    Counter[str, int]     = Counter()

  def isValid(
    self,
    unscheduled: Optional[Counter[scenario.Process, int]],
    update: Update
  ) -> bool:
    # SCHEDULE: processes must be in unscheduled
    if update.type is UpdateType.Schedule:
      if unscheduled is None:
        return False
      # every process count in update ≤ count in unscheduled
      for proc, cnt in update.processes.items():
        if unscheduled[proc] < cnt:
          return False
      return True

    # RUN: must be scheduled, and buffer must cover all inputs
    if update.type is UpdateType.Run:
      # (a) subset of scheduled
      for proc, cnt in update.processes.items():
        if self.scheduled[proc] < cnt:
          return False
      # (b) buffer covers inputs
      # compute total required tokens
      required: Counter[str, int] = Counter()
      for proc, cnt in update.processes.items():
        for token, need in proc.inputs.items():
          required[token] += need * cnt
      for token, need in required.items():
        if self.buffer[token] < need:
          return False
      return True

    # FINISH: must be running
    if update.type is UpdateType.Finish:
      for proc, cnt in update.processes.items():
        if self.running[proc] < cnt:
          return False
      return True

    return False

  def update(self, update: Update) -> None:
    if not self.isValid(None if update.type is UpdateType.Schedule else None, update):
      raise RuntimeError(f"Invalid update: {update.type}")

    if update.type is UpdateType.Schedule:
      # move from external unscheduled into scheduled;
      # external removal from unscheduled is handled elsewhere
      self.scheduled.update(update.processes)

    elif update.type is UpdateType.Run:
      # (a) add to running
      self.running.update(update.processes)
      # (b) remove from scheduled
      for proc, cnt in update.processes.items():
        self.scheduled[proc] -= cnt
        if self.scheduled[proc] == 0:
          del self.scheduled[proc]
      # (c) remove consumed tokens
      for proc, cnt in update.processes.items():
        for token, need in proc.inputs.items():
          self.buffer[token] -= need * cnt
          if self.buffer[token] == 0:
            del self.buffer[token]

    elif update.type is UpdateType.Finish:
      # (a) remove from running
      for proc, cnt in update.processes.items():
        self.running[proc] -= cnt
        if self.running[proc] == 0:
          del self.running[proc]
      # (b) add outputs to buffer
      for proc, cnt in update.processes.items():
        for token, out in proc.outputs.items():
          self.buffer[token] += out * cnt

  def print_workstation(self) -> None:
    print(f"scheduled: {dict(self.scheduled)}")
    print(f"running:   {dict(self.running)}")
    print(f"buffer:    {dict(self.buffer)}")
