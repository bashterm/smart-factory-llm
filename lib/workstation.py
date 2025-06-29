from collections                 import Counter
from enum                        import Enum
from lib.workstation_interpreter import ActivityType


class Workstation:

  def __init__(self):

    # Workstation State
    self.scheduled = Counter()    # The multiset of scheduled processes
    self.running   = Counter()    # The multiset of running   processes
    self.finished  = Counter()    # The multiset of finished  processes
    self.buffer    = Counter()    # The tokens in the workstation's buffer

  def check_activity_feasibility_and_update_state(self, activity):

    process_quantities = Counter({pq.process : pq.quantity for pq in activity.process_quantities})

    if activity.activity_type   == ActivityType.SCHEDULE:
      self.scheduled += process_quantities

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


  def print_workstation(self):
    print(f"scheduled: {dict(self.scheduled)}")
    print(f"running:   {dict(self.running)}")
    print(f"buffer:    {dict(self.buffer)}")
