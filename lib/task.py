class AgentTaskType:
  DEPOSIT = 1 
  PICK    = 2

class AgentTask:

  def __init__(self, target, task_type):
    self.target    = target      # A machine or workstation
    self.task_type = task_type   # Deposit or pick up
    self.tokens    = tokens      # Multiset of tokens to pick or deposit