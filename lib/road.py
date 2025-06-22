from collections          import deque

import lib.utilities      as ut

class Road:

  def __init__(self, junction_st, junction_en, path):

    self.id                 = f"{junction_st.id}->{junction_en.id}"   # Map state
    self.junction_st        = junction_st                         
    self.junction_en        = junction_en
    self.path               = path
    self.midpoint           = junction_st.cell.avg(junction_en.cell)

  def next_cell(self, cell):

    if cell == self.path[-1]:
      return self.junction_en.cell

    elif cell in self.path[:-1]:
      cell_index = self.path.index(cell)
      return self.path[cell_index + 1]

    else:
      assert False, f"Road {self.id}: next_cell called with cell {cell} not in path {self.path}"

  def __repr__(self):
    return self.id

  def print_road(self):
    print((f"road:{self.id} junction_st:{self.junction_st} "
           f"junction_en:{self.junction_en} path:{self.path}"))