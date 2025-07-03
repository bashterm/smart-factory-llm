import json
import lib.utilities             as     util

from collections                 import Counter
from lib.workstation_interpreter import ActivityType


# Installations run processes
class Installation:

  def __init__(self, description):

    # Installation Location
    self.input_cell  = util.Pt(*description["input"])  if description["input"] else None
    self.output_cell = util.Pt(*description["output"]) if description["output"] else None
    self.label_cell  = util.Pt(*description["label"])

    # Installation State
    self.scheduled = Counter()    # The multiset of scheduled processes
    self.running   = Counter()    # The multiset of running   processes
    self.finished  = Counter()    # The multiset of finished  processes
    self.buffer    = Counter()    # The tokens in the workstation's buffer

  def print_state(self):
    print(f"scheduled: {dict(self.scheduled)}")
    print(f"running:   {dict(self.running)}")
    print(f"finished:  {dict(self.finished)}")
    print(f"buffer:    {dict(self.buffer)}")

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


  def check_activity_feasibility_and_update(self, coordinator, activity):

    process_quantities = Counter({pq.process.value : pq.quantity 
                                  for pq in activity.process_quantities})
    coordinator.print_unassigned_processes()


    if activity.activity_type   == ActivityType.SCHEDULE:
      if not process_quantities <= coordinator.unassigned:
        msg = (f"The update schedules the multiset of processes {process_quantities}. "
               f"But the multiset of processes which still need to be scheduled is "
               f"{coordinator.unassigned}. You can't schedule unnecessary processes!")
        return msg

      coordinator.unassigned -= process_quantities
      self.scheduled         += process_quantities

    elif activity.activity_type == ActivityType.RUN:
      if not process_quantities <= self.scheduled:
        msg = (f"The update runs the multiset of processes {process_quantities}. "
               f"But the multiset of processes scheduled is {self.scheduled}. "
               f"You can't run processes that aren't scheduled!")
        return msg

      self.scheduled -= process_quantities
      self.running   += process_quantities

    elif activity.activity_type == ActivityType.FINISH:
      if not process_quantities <= self.running:  
        msg = (f"The update finishes the multiset of processes {process_quantities}. "
               f"But the multiset of processes running is {self.running}. "
               f"You can't run finish processes that aren't running!") 
        return msg

      self.running  -= process_quantities
      self.finished += process_quantities

    else:
      raise RuntimeError(f"Did not recognize activity type {activity.activity_type}")

    return None


def build_installations(path):

  with open(path) as file:
    installation_descriptions = json.loads(file.read())

  # Installations are machines or workstations
  machines     = {}
  workstations = {}

  # Load each installation
  for installation_id, description in installation_descriptions.items():
    if   description["type"] == "machine":
      machines[installation_id] = Machine(description)
    elif description["type"] == "workstation":
      workstations[installation_id] = Workstation(description)
    else:
      raise RuntimeError(f"Did not recognize installation type:{description['type']}")

  return machines, workstations


def print_installations(machines, workstations):
  for mid, machine in machines.items():
    print(f"Machine {mid}: {repr(machine)}")
  for wid, workstation in workstations.items():
    print(f"Workstation {wid}: {repr(workstation)}")