class Junction:
  
  def __init__(self, cell):
    self.id   = str(cell) 
    self.rIn  = []
    self.rOut = []
    self.cell = cell

  def __str__(self):
    return self.id