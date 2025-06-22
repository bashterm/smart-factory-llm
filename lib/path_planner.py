import lib.utilities      as util
from typing               import List, Literal, Optional, Tuple, Union
from pydantic             import BaseModel

# Junction Name Format
class JunctionName(BaseModel):
  x: int
  y: int

  def __repr__(self):
    return f"({self.x},{self.y})"

# Reasoning Step Format
class ReasoningStep(BaseModel):
  reasoning: str

# Condition Effect Format
class ConditionEffect(BaseModel):
  condition_effect: str

# Path Proposal Format
class Path(BaseModel):
  important_condition_effect: ConditionEffect
  other_conditions_effect: List[ConditionEffect]
  reasoning_steps: List[ReasoningStep]
  path: List[JunctionName]

  def format_path(self):

    # Format condition effects
    proposal_str  = "[SUBSECTION 1: CONDITION EFFECTS]\n"

    for i, effect in enumerate([self.important_condition_effect] + self.other_conditions_effect):
      proposal_str += f"Effect {i+1}: {effect.condition_effect}\n"

    # Format reasoning
    proposal_str += "[SUBSECTION 2: REASONING]\n"

    for i, reasoning_step in enumerate(self.reasoning_steps):
      proposal_str += f"Step {i+1}: {reasoning_step.reasoning}\n"

    # Format path
    proposal_str += "[SUBSECTION 3: PATH]\n"
    proposal_str += f"{self.path}"

    return proposal_str


# Condition Score Format
class ConditionScore(BaseModel):
  reasoning_steps: List[ReasoningStep]
  score: int

  def print_condition_score(self):
    print(f"[REASONING]")
    for i, reasoning_step in enumerate(self.reasoning_steps): 
      print(f"Step {i+1}: {reasoning_step.reasoning}")
    print(f"[SCORE]\n{self.score}")

class PathPlanner:

  def __init__(self, proposer_model, aggregator_models):
    
    # Set up LLMs
    self.proposers   = util.EnsembleInterface(proposer_models, Path)
    self.aggregators = util.EnsembleInterface(aggregator_models, Path)

    # Set up prompts
    with open("prompts/map_proposer_prompt.txt", "r")   as file:
      self.proposer_prompt_template = file.read()

    with open("prompts/map_aggregator_prompt.txt", "r") as file:
      self.aggregator_prompt_template = file.read()

    with open("prompts/map_filter_prompt.txt", "r")     as file:
      self.filter_prompt_template = file.read()

    with open("prompts/map_judge_prompt.txt", "r")      as file:
      self.judge_prompt_template = file.read()



  def plan_junction_path(self, factory_map, start_cell, goal_cell):

    # Get start and goal junction
    start_junction = self.get_start_junction(factory_map, start_cell)
    goal_junction  = self.get_goal_junction(factory_map, goal_cell)
    print(f"start_junction:{start_junction} goal_junction:{goal_junction}")
    
    # Proposers: Generate a series of paths between the start and the goal junctions
    paths = self.propose_paths(factory_map, start_junction, goal_junction)

    # Aggregators: Synthesize the proposer's path proposals
    paths = self.aggregate_paths(factory_map, start_junction, goal_junction, paths)

    # Filters: Filter each path 
    paths = self.filter_paths(factory_map, start_junction, goal_junction, paths)

    # Judges: Select a path proposal
    path  = self.judge_paths(factory_map, start_junction, goal_junction, paths)
    return path


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
  def propose_paths(self, factory_map, start_junction, goal_junction):

    traces = []

    for i, priority_condition in enumerate(factory_map.conditions): 

      other_conditions = factory_map.conditions[:i] + factory_map.conditions[i+1:]

      proposer_prompt = (
        self.proposer_prompt_template
            .replace("{junctions}",          self.format_junctions(factory_map.junctions))
            .replace("{roads}",              self.format_roads(factory_map.roads))
            .replace("{priority_condition}", priority_condition)
            .replace("{other_conditions}",   self.format_conditions(other_conditions))
            .replace("{start_junction}",     repr(start_junction.cell))
            .replace("{goal_junction}",      repr(goal_junction.cell))
        )

      traces.append([util.Message("user", proposer_prompt)])

    raw_path_proposals = self.proposers.evaluate_traces(traces)
    return [raw_path_proposal.parsed for raw_path_proposal in raw_path_proposals]

  # The aggregators then synthesize the path proposals
  def aggregate_paths(self, factory_map, start_junction, goal_junction, paths):

    aggregator_prompt = (
      self.aggregator_prompt_template
        .replace("{junctions}",          self.format_junctions(factory_map.junctions))
        .replace("{roads}",              self.format_roads(factory_map.roads))
        .replace("{conditions}",         self.format_conditions(factory_map.conditions))
        .replace("{num_path_proposals}", len(paths))
        .replace("{start_junction}",     repr(start_junction.cell))
        .replace("{goal_junction}",      repr(goal_junction.cell))
      )


    for i, path in enumerate(paths):

      aggregator_prompt += f"[SECTION {i+5}: PATH PROPOSAL {i+1}]\n"
      aggregator_prompt += path.format_path()
      aggregator_prompt += "\n"

    traces = [aggregator_prompt] * len(self.aggregators)
    raw_path_proposals = self.proposers.evaluate_traces(traces)
    return [raw_path_proposal.parsed for raw_path_proposal in raw_path_proposals]



  def filter_paths(self, factory_map, start_junction, goal_junction, path_proposals):

    # Generate traces
    id_to_trace = {}

    for proposal_id, path_proposal in enumerate(path_proposals):
      for condition_id, filter_condition in enumerate(factory_map.conditions):

        filter_prompt = (
          self.filter_prompt_template
              .replace("{junctions}",        self.format_junctions(factory_map.junctions))
              .replace("{roads}",            self.format_roads(factory_map.roads))
              .replace("{conditions}",       self.format_conditions(factory_map.conditions))
              .replace("{filter_condition}", filter_condition)
              .replace("{start_junction}",   repr(start_junction.cell))
              .replace("{goal_junction}",    repr(goal_junction.cell))
              .replace("{path_proposal}",    path_proposal.format_path()))

        id_to_trace[(proposal_id, condition_id)] = [util.Message("user", filter_prompt)]


    # Judge traces
    ensemble_interface    = util.ScalingEnsembleInterface("gpt-4o", ConditionScore)
    id_to_response        = ensemble_interface.evaluate_traces(id_to_trace)

    condition_score = {trace_id:response.parsed for trace_id,response in id_to_response.items()}


    # Filter out any proposal which did not satisfy one of the factory conditions
    filtered_path_proposals = []
    for proposal_id, path_proposal in enumerate(path_proposals):

      if all(condition_score[(proposal_id, condition_id)].score > 40 
             for condition_id in range(len(factory_map.conditions))):
        
        filtered_path_proposals.append(path_proposal)

    return filtered_path_proposals

      
  def judge_paths(self, factory_map, start_junction, goal_junction, path_proposals):
    
    judge_prompt = (
      self.judge_prompt_template
        .replace("{junctions}",          self.format_junctions(factory_map.junctions))
        .replace("{roads}",              self.format_roads(factory_map.roads))
        .replace("{conditions}",         self.format_conditions(factory_map.conditions))
        .replace("{num_path_proposals}", len(paths))
        .replace("{start_junction}",     repr(start_junction.cell))
        .replace("{goal_junction}",      repr(goal_junction.cell))
      )


    for i, path in enumerate(paths):

      judge_prompt += f"[SECTION {i+5}: PATH PROPOSAL {i+1}]\n"
      judge_prompt += path.format_path()
      judge_prompt += "\n"

    traces = [judge_prompt] * len(self.judges)
    raw_path_proposals = self.proposers.evaluate_traces(traces)
    return [raw_path_proposal.parsed for raw_path_proposal in raw_path_proposals]


  # Formats junctions to be added to a prompt
  def format_junctions(self, junctions):
    return ", ".join([repr(junction.cell) for junction in junctions])

  # Formats roads to be added to a prompt
  def format_roads(self, roads):
    return ", ".join([road.id for road in roads])

  # Formats conditions to be added to a prompt
  def format_conditions(self, conditions):
    return "\n".join([f"-- {condition}" for condition in conditions])

  # Prints each path
  def print_paths(self, paths):
    for i, path in enumerate(paths): 
      print(f"[PATH PROPOSAL {i+1}]\n{path.format_path()}")












