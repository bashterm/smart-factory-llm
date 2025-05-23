from   itertools            import product
from   json                 import load
from   lib.junction         import Junction
from   lib.road             import Road

import lib.utilities        as     util
import matplotlib.pyplot    as     plt
import networkx             as     nx


class Map():

  def __init__(self, path, installations):

    # (1) Load Map
    with open(path) as file:
      self.map = [l.strip() for l in file.readlines()]

    # (2) Get Map Dimensions
    self.nrows = len(self.map)
    self.ncols = len(self.map[0])

    # (3) Get junctions, input, output, workstation and machine cells
    self.junctions         = []
    input_cells            = []    # Installation input cells
    output_cells           = []    # Installation output cells
    self.workstation_cells = []    # Cells occupied by a workstation
    self.machine_cells     = []    # Cells occupied by a machine

    for x,y in product(range(self.ncols), range(self.nrows)):
      cell = util.Pt(x, y)

      match self.at(cell):
        case "!":
          self.junctions.append(Junction(cell))
        case "t":
          self.workstation_cells.append(cell)
        case "#":
          self.machine_cells.append(cell)

    # (4) Get Roads
    self.roads        = []
    cell_to_junction  = {repr(junction.cell):junction for junction in self.junctions}

    for junction_st, direction_v in product(self.junctions, util.direction_to_v.values()):
      
      # Check if each cell adjacent to a junction is a start of a road
      cell_st         = junction_st.cell.add(direction_v)

      if not self.in_map(cell_st) or self.at(cell_st) not in "NEWS":                                 # Ensure road begins at st
        continue
                   
      # Get the road's path and end junction
      path, junction_en = self.get_path(cell_st, cell_to_junction)
      road = Road(junction_st, junction_en, path)
      
      self.roads.append(road)
      junction_st.rOut.append(road)
      junction_en.rIn.append(road)

    for road in self.roads:
      road.print_road()

  def in_map(self, pt):
    return 0 <= pt.x < self.ncols and 0 <= pt.y < self.nrows

  def at(self, pt):
    return self.map[self.nrows - pt.y - 1][pt.x] if self.in_map(pt) else None

  def get_path(self, cell_st, cell_to_junction):

    path = []
    cell = cell_st

    while self.at(cell) != "!":

      cell_direction = self.at(cell).lower()
      assert cell_direction in ["n", "e", "w", "s"], f"Path terminates at a {self.at(cell)} cell!"

      path.append(cell)
      cell = cell.add(util.direction_to_v[cell_direction])

    return path, cell_to_junction[repr(cell)]

  def graph_visualizer(self):
    G      = nx.DiGraph()
    G.add_nodes_from(self.junctions)
    G.add_nodes_from(self.roads)
    G.add_edges_from([(road.junction_st, road) for road in self.roads])
    G.add_edges_from([(road, road.junction_en) for road in self.roads])
    pos    = {junction:junction.cell.to_tuple() for junction in self.junctions}
    pos.update({road:road.midpoint.to_tuple() for road in self.roads})
    v_lbls = {v:v.id for v in G.nodes()}
    return G, pos, v_lbls

  def visualize(self):
    G, pos, v_lbls = self.graph_visualizer()
    nx.draw(G, pos=pos, labels=v_lbls)
    plt.show() 



