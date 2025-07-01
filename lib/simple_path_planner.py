import lib.utilities    as     util

from   lib.path_planner import PathProposal


class SimplePathPlanner:

  def __init__(self, path_planner_model):
    
    self.path_planner_LLM = util.LLMInterface(path_planner_model, PathProposal)

    with open("prompts/ablated_map_proposer_prompt.txt", "r")   as file:
      self.proposer_prompt_template = file.read()


  def plan_junction_path(self, factory_map, start_cell, goal_cell):

    # Get start and goal junction
    start_junction = self.get_start_junction(factory_map, start_cell)
    goal_junction  = self.get_goal_junction(factory_map, goal_cell)
    print(f"start_junction:{start_junction} goal_junction:{goal_junction}")

    path_proposal = self.propose_path(factory_map, start_junction, goal_junction)
    print(path_proposal.format_path())
    return path_proposal.path


  # Get the junction at the end of the road which contains start_cell
  def get_start_junction(self, factory_map, start_cell):
    for road in factory_map.roads:
      if start_cell in road.path:
        return road.junction_en
    raise RuntimeError(f"Start cell {start_cell} is not in any road!")


  # Get the junction at the beginning of the road which contains end_cell
  def get_goal_junction(self, factory_map, goal_cell):
    for road in factory_map.roads:
      if goal_cell in road.path:
        return road.junction_st
    raise RuntimeError(f"Goal cell {goal_cell} is not in any road!")


  # We ask the proposers to generate paths from the start junction to the goal junction
  def propose_path(self, factory_map, start_junction, goal_junction):

    path_proposer_prompt = (
      self.proposer_prompt_template
          .replace("<junctions>",          self.format_junctions(factory_map.junctions))
          .replace("<roads>",              self.format_roads(factory_map.roads))
          .replace("<conditions>",         self.format_conditions(factory_map.conditions))
          .replace("<start_junction>",     repr(start_junction.cell))
          .replace("<goal_junction>",      repr(goal_junction.cell))
      )

    input(path_proposer_prompt)

    to_send  = [util.Message("user", path_proposer_prompt).__dict__]
    return self.path_planner_LLM.evaluate_trace(to_send).parsed


  # Formats junctions to be added to a prompt
  def format_junctions(self, junctions):
    return ", ".join([repr(junction.cell) for junction in junctions])

  # Formats roads to be added to a prompt
  def format_roads(self, roads):
    return ", ".join([road.id for road in roads])

  # Formats conditions to be added to a prompt
  def format_conditions(self, conditions):
    return "\n".join([f"-- {condition}" for condition in conditions])











