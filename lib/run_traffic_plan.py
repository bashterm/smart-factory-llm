import lib.traffic_ilp_helpers   as     ilp
import lib.visualizer            as     visualizer

from   itertools                 import product
from   math                      import floor

class RunTrafficPlan():

  def __init__(self, procedure, machines, m, plan, num_epochs, timesteps_per_epoch):

    # Set up the problem
    self.null_token      = procedure.null_token
    self.non_null_tokens = procedure.non_null_tokens

    # Set up visualizer
    self.visualizer = visualizer.Visualizer(m, machines, procedure)

    # Initialize factory state
    self.t = -1
    self.T = -1

    # Initialize agent state
    self.at  = {}
    self.has = {}

    # Agent counter
    agent_id = 0

    # Position outB(road, 0, zj) agents carrying token zj in the queue at the head of the road at timestep t=0
    for road in m.roads:

      # The index of the next free cell in the road
      free_ind = len(road.path) - 1   

      for zj in procedure.tokens:

        # Number of tokens to add to the road
        to_add = int(plan.var[ilp.outbound_var(road.id, 0, zj)].x)

        while to_add > 0:
          
          # Get the next free road cell in the road
          # print(f"road:{road.id} path:{road.path} free_ind:{free_ind}")
          agent_cell  = road.path[free_ind]
          free_ind   -= 1

          # Place an agent on agent_cell carrying token zk
          self.at[agent_cell] = agent_id
          self.has[agent_id]  = zj

          # print(f"agent_id:{agent_id}, at:{agent_cell}, has:{self.has[agent_id]}")  

          agent_id           += 1
          to_add             -= 1       

    self.total_agents = agent_id

    # Initialize epoch plan storage
    self.inbound         = {}
    self.deposited       = {}
    self.pickedup        = {}
    self.last_transition = {agent:-1 for agent in range(self.total_agents)}

  
    while True:
      self.timestep(procedure, machines, m, plan, num_epochs, timesteps_per_epoch)


  def timestep(self, procedure, machines, m, plan, num_epochs, timesteps_per_epoch):

    # Create dictionaries which store each agent's state on the next timestep
    self.next_at  = {}
    self.next_has = {}

    # Update t and T
    self.t += 1

    if self.t % timesteps_per_epoch == 0:
      self.T  += 1
      self.initialize_epoch_plan(procedure, machines, m, plan, num_epochs)

    self.visualizer.generate_state(self.at, self.has)
    self.print_status_at_start_of_timestep(procedure, machines, m, plan, num_epochs)

    # Move agents on junctions
    for junction in m.junctions:
      self.move_agents_on_junction(junction)

    # Move agents on roads
    for road in m.roads:
      self.move_agents_on_road(road)

    self.at  = self.next_at

    # Deposit tokens
    self.deposit_tokens(machines, m)
    self.pickup_tokens(machines, m)
    self.keep_tokens()

    # Check for vanishing tokens
    self.check_for_vanishing_agents()

    self.has = self.next_has


  def initialize_epoch_plan(self, procedure, machines, m, plan, num_epochs):

    target_T = self.T % num_epochs        # The epoch in the plan that we will copy

    # Add the number of agents inbound to each road on epoch T to its plan
    for road, zj in product(m.roads, procedure.tokens):
      self.inbound[(road.id, self.T, zj)]   = plan.var[ilp.inbound_var(road.id, target_T, zj)].x

    for mid in machines.supported_processes.keys():

      # Add the number of tokens deposited at each machine during epoch T to its plan
      for zj in machines.possibly_consumed_tokens[mid]:
        self.deposited[(mid, self.T, zj)] = plan.var[ilp.deposit_var(mid, target_T, zj)].x

      # Add the number of tokens picked up from each machine during epoch T to its plan
      for zj in machines.possibly_produced_tokens[mid]:
        self.pickedup[(mid, self.T, zj)] = plan.var[ilp.pickup_var(mid, target_T, zj)].x
    

  # Moves the agent on a junction
  def move_agents_on_junction(self, junction):

    if not junction.pt in self.at:
      return

    agent_id = self.at[junction.pt]

    for road in junction.rOut:
      if self.inbound[(road.id, self.T, self.has[agent_id])] > 0:

        # Update agent position
        self.next_at[road.path[0]] = agent_id

        # Reduce the number of agents that need to enter the road this epoch
        self.inbound[(road.id, self.T, self.has[agent_id])] -= 1

        # Note that the agent transitioned on this epoch
        self.last_transition[agent_id] = self.T
        return

    assert False, f"Agent {agent_id} on junction {junction.id} not needed for any next road"


  # Moves each agent on a road
  def move_agents_on_road(self, road):

    for cell in reversed(road.path):

      if cell in self.at:
        agent_id = self.at[cell]

        # The cell that the agent will move to next
        next_cell = road.next_cell(cell)

        # Agent waits if next cell is a junction and it has already swapped roads this epoch
        if self.last_transition[agent_id] == self.T and next_cell == road.J_en.pt:
          self.next_at[cell]      = agent_id

        # Agent waits on its current cell if its next cell is occupied
        elif next_cell in self.next_at:
          self.next_at[cell]      = agent_id

        # Otherwise, agent moves to its next cell
        else:
          self.next_at[next_cell] = agent_id


  # Checks to see if each agent should deposit its token
  def deposit_tokens(self, machines, m):

    # For each input cell in the map
    for road in m.roads:
      for cell, mid in road.input_cell_to_mid.items():

        # If there is no agent on the input cell, continue
        if cell not in self.at:
          continue

        # Agent on cell
        agent_id = self.at[cell]  

        # If the agent is not carrying a token that mid needs, continue
        if self.has[agent_id] not in machines.possibly_consumed_tokens[mid]:
          continue

        # Temp initialization thing
        if self.last_transition[agent_id] == -1:
          continue

        # If the machine mid needs a copy of the token that the agent is carrying from agents that entered
        # the road on epoch self.last_transition[agent_id], deposit the agent's token
        if self.deposited[(mid, self.last_transition[agent_id], self.has[agent_id])] > 0:
          self.deposited[(mid, self.last_transition[agent_id], self.has[agent_id])] -= 1
          self.next_has[agent_id] = self.null_token

          print(f"Update: Agent {agent_id} token {self.has[agent_id]} dep({mid}, {self.last_transition[agent_id]})")



  # Checks to see if each agent should pick up a token
  def pickup_tokens(self, machines, m):

    # For each output cell in the map
    for road in m.roads:
      for cell, mid in road.output_cell_to_mid.items():

        # If there is no agent on the output cell, continue
        if cell not in self.at:
          continue

        # Agent on cell
        agent_id = self.at[cell]  

        # If the agent is carrying a token, continue
        if self.has[agent_id] != self.null_token:
          continue

        # Temp initialization thing
        if self.last_transition[agent_id] == -1:
          continue

        # If the machine mid needs a token in its output buffer picked up by an agent that entered the road on 
        # epoch self.last_transition[agent_id], pick up a token 
        for zj in machines.possibly_produced_tokens[mid]:
          if self.pickedup[(mid, self.last_transition[agent_id], zj)] > 0:
            self.next_has[agent_id] = zj
            self.pickedup[(mid, self.last_transition[agent_id], zj)] -= 1

            print(f"Update: Agent {agent_id} token {self.next_has[agent_id]} pck({mid}, {self.last_transition[agent_id]})")


  # If an agent has not picked up or deposited a token this timestep, continue
  def keep_tokens(self):
    for agent_id in range(self.total_agents):
      if agent_id not in self.next_has:
        self.next_has[agent_id] = self.has[agent_id]


  # Make sure that no agent has vanished
  def check_for_vanishing_agents(self):
    assert len(self.next_at)  == self.total_agents
    assert len(self.next_has) == self.total_agents


  # Print starting timestep details
  def print_status_at_start_of_timestep(self, procedure, machines, m, plan, num_epochs):
    print(f"At start of t={self.t}, T={self.T}")
    print(f"{self.at}")

    for cell, agent_id in sorted(self.at.items(), key=lambda item: item[1]):
      print(f"Agent {agent_id} on cell {cell} with token {self.has[agent_id].name}")


    target_t = self.T % num_epochs

    print(f"---- t={self.t}, T={self.T} ({target_t}) inbound ----")

    for road in m.roads:
      r_status_str  = f"Road {road.id} needs "

      for zj in procedure.tokens:
        tokens_needed       = abs(self.inbound[(road.id, self.T, zj)])
        total_tokens_needed = abs(plan.var[ilp.inbound_var(road.id, target_t, zj)].x)

        if total_tokens_needed > 0:
          r_status_str += f"{zj.name:} {tokens_needed:.0f}/{total_tokens_needed:.0f}   "

      print(r_status_str)

    print(f"---- t={self.t}, T={self.T} tokens ----")

    for road in m.roads:

      r_token_str = f"Road {road.id} needs "

      for cell, mid in road.input_cell_to_mid.items(): 
        for T in [self.T, self.T-1 % num_epochs]:
          for zj in machines.possibly_consumed_tokens[mid]:
            to_dep       = abs(self.deposited[(mid, T, zj)])
            total_to_dep = abs(plan.var[ilp.deposit_var(mid, target_t, zj)].x)

            if total_to_dep > 0:
              r_token_str += f"{zj.name:} {to_dep:.0f}/{total_to_dep:.0f} dep({mid},{T})  " 

          if num_epochs == 1:
            break


      for cell, mid in road.output_cell_to_mid.items(): 
        for T in [self.T, self.T-1 % num_epochs]:
          for zj in machines.possibly_produced_tokens[mid]:
            to_pck       = abs(self.pickedup[(mid, T, zj)])
            total_to_pck = abs(plan.var[ilp.pickup_var(mid, target_t, zj)].x)

            if total_to_pck > 0:
              r_token_str += f"{zj.name:} {to_pck:.0f}/{total_to_pck:.0f} pck({mid},{T})   " 

          if num_epochs == 1:
            break

      print(r_token_str)

    input("Continue?")