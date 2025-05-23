from lib.scenario import VALID_ORIENTATIONS, Machine


import json
import random
from enum import Enum


class Layout:
  __slots__ = ('floorplan', 'machines', 'timesteps', 'agent_limit')

  def __init__(self, floorplan, machines, timesteps, agent_limit):
    self.floorplan = floorplan
    self.machines = machines
    self.timesteps = timesteps
    self.agent_limit = agent_limit

  @staticmethod
  def from_dict(info, blueprints):
    floorplan = [list(row) for row in info['floorplan'][::-1]]

    machines = [Machine(machine_id=mid,
                        blueprint=blueprints.get_blueprint(
                          blueprints.machine_types[m['mtype']]),
                        position=m['pos'],
                        orientation=m['orientation'])
                for mid, m in enumerate(info['machines'])]

    timesteps = int(info['timesteps'])
    agent_limit = int(info['agent_limit'])

    return Layout(floorplan, machines, timesteps, agent_limit)

  @staticmethod
  def from_layout_file(path, blueprints):
    """
    Method for loading a layout from a json layout file
    """
    with open(path) as file:
      info = json.loads(file.read())

    return Layout.from_dict(info, blueprints)
    

  def to_dict(self):
    return {
      "floorplan": self.floorplan[::-1],
      "machines" : [machine.to_dict() for machine in self.machines],
      "timesteps": self.timesteps,
      "agent_limit": self.agent_limit
    }

  @staticmethod
  def pick_point_in_layout(layout):
    y, x = (int(random.random() * len(layout)), int(random.random() * len(layout[0])))
    if layout[y][x] != '.':
      return Layout.pick_point_in_layout(layout)
    return (x, y)  # Return X, Y here since machine class expects it for positioning

  @staticmethod
  def from_seed_dict(info, blueprints):
    """
    Method for creating a random layout from a seed layout dict
    """

    floorplan = [list(row) for row in info['floorplan'][::-1]]

    machines = [
      Machine(
          mid,
          blueprints.get_blueprint(blueprints.machine_types[m_type]),
          Layout.pick_point_in_layout(floorplan),
          random.choice(VALID_ORIENTATIONS)
        )
      for mid, m_type in enumerate([mtype for mgroup in [[m_type] * count for m_type, count in info['machines'].items()] for mtype in mgroup])
    ]

    timesteps = random.choice(range(info['min_timesteps'], info['max_timesteps']))

    return Layout(floorplan, machines, timesteps)

  def get_emitting_machines(self, token: Enum):
    return [m for m in self.machines if token in m.blueprint.get_possible_output_tokens()]

  def get_consuming_machines(self, token: Enum):
    return [m for m in self.machines if token in m.blueprint.get_possible_input_tokens()]