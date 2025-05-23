from collections import Counter

class Agent:

  def __init__(self, agent_id, cell):

    # Agent State
    self.id    = agent_id
    self.cell  = cell
    self.cargo = Counter()

    # Agent Task Information
    self.scheduled_tasks = []
    self.road_path       = []
    self.goal_cell       = []
    self.goal_action     = None


  def add_cargo(self, cargo):
    self.cargo += cargo

  def remove_cargo(self, cargo):

    if not cargo <= self.cargo:
      raise RuntimeError(f"Can't remove cargo {cargo} from agent {self.id} (cargo:{self.cargo})")

    self.cargo -= cargo
