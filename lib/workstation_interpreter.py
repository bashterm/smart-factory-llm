import lib.utilities as ut
import math
import tiktoken

from collections          import Counter
from concurrent.futures   import ThreadPoolExecutor
from enum                 import Enum
from typing               import List, Literal, Optional, Tuple, Union
from pydantic             import BaseModel


###################################
# The Intrepreter Response Schema #
###################################

# The possible activity types
class ActivityType(Enum):
  SCHEDULE = 1 
  RUN      = 2
  FINISH   = 3

# An process:item entry 
class ProcessQuantity(BaseModel):
  process:  Literal["carve_chassis", "carve_wheel", "assemble_car"]
  quantity: int

# When we’ve understood the update, we formalize it
class Activity(BaseModel):
  activity_type: ActivityType
  processes:     List[ProcessQuantity]

  # Convert this class into a hashable tuple key of the form:
  # (activity_type, ((process, quantity), (process, quantity), ...))
  def to_tuple(self) -> Tuple[ActivityType, Tuple[Tuple[str, int], ...]]:
    processes_tuple = tuple((pq.process, pq.quantity) for pq in self.processes)
    return (self.activity_type, processes_tuple)

# When we need more information, we ask a question
class Question(BaseModel):
  question: str

# When the system gives us information, we acknowledge it
class Ack(BaseModel):
  ack: Literal["ack"]

# Top level Response
class Response(BaseModel):
  root: Union[Activity, Question, Ack]

# A message in the trace
class Message:
  def __init__(self, role, content):
    self.role:    str = role
    self.content: str = content

  def __repr__(self):
    return f"{self.role}: {self.content}"

class InterpreterGamma:

  def __init__(self, models):

    # Initialize interpreter
    self.llms           = [ut.LLMInterface(model, Response) for model in models]
    self.trace          = []

    with open("prompts/interpreter_prompt3.txt", "r") as file:
      interpreter_prompt = file.read()
      self.trace.append(Message("system", interpreter_prompt))

    # Initialize workstation state
    self.scheduled = Counter()
    self.running   = Counter()
    self.finished  = Counter()

    # The culmulative token lengths of the messages in the trace. The last message in the trace has 
    # a culmulative token length of tkLen(message[-1]). The second-to-last has culmulative token 
    # length of tkLen(message[-2]) + tkLen(message[-1]) and so on.
    self.culmulative_tokens = []

    # Information to help us compute encoding length
    self.encoding = tiktoken.encoding_for_model("gpt-4o")
    self.tokens_per_message = 4

  def main(self):

    self.get_response_from_user("What is your first update?")

    while True:

      to_send  = [message.__dict__ for message in self.trace]
      response = self.generate_response(to_send)
      

      # 3) If response is a question, pass it on to the user
      if isinstance(response, Question):
        self.get_response_from_user(response_root.question)

      # 4) If response is an acknowledgement, ask the user for the next question
      elif isinstance(response, Ack):
        self.get_response_from_user("What is your next update?")

      # 5) If response is an activity, update the workstation's status
      elif isinstance(response, Activity):
        err_msg = self.check_and_update_status(response)
        to_llm  = f"system - invalid:{err_msg}" if err_msg else f"system - valid"
        self.store_response(Message("user", to_llm))

        
  def get_response_from_user(self, to_user: str) -> None:
    from_user = input(to_user)
    self.store_response(Message("user", "from_user"))
    

  def check_and_update_status(self, activity: Activity) -> Optional[str]:

    processes = Counter({pq.process:pq.quantity for pq in activity.processes})

    if activity.activity_type == ActivityType.SCHEDULE:
      self.scheduled += processes
 
    elif activity.activity_type == ActivityType.RUN:
      if not processes <= self.scheduled:
        msg = (f"The update runs the multiset of processes {processes}. "
               f"But the multiset of processes scheduled is {self.scheduled}. "
               f"You can't run processes that aren't scheduled!")
        return msg

      self.scheduled -= processes
      self.running   += processes

    elif activity.activity_type == ActivityType.FINISH:
      if not processes <= self.running:  
        msg = (f"The update finishes the multiset of processes {processes}. "
               f"But the multiset of processes running is {self.running}. "
               f"You can't run finish processes that aren't running!") 
        return msg

      self.running  -= processes
      self.finished += processes

    else:
      raise RuntimeError(f"Did not recognize activity type {activity.activity_type}")

    return None


  def print_trace(self):
    for i, message in enumerate(self.trace[1:]):
      print(f"message {i+1}:{repr(message)}")

  def generate_one_response(self, to_send):

    # 1) Get a response to current trace from the LLM
    self.print_trace()
    to_send  = [message.__dict__ for message in self.trace]
    response = self.llm.evaluate_prompt(to_send)

    # 2) Extract and store the response
    new_message     = Message("assistant", str(response.parsed))
    self.trace.append(new_message)
    return response.parsed.root


  def store_response(self, message: Message):

    # Add message to trace
    self.trace.append(message)

    # Compute message's token length
    token_len = len(self.encoding.encode(text)) + self.tokens_per_message

    # Update cumulative tokens
    self.culmulative_tokens.append(0)
    self.culmulative_tokens = [prev_len + token_len for prev_len in self.culmulative_tokens]


  def generate_response(self, to_send):

    with ThreadPoolExecutor(max_workers=len(self.llms)) as executor:

      self.print_trace()

      futures       = [executor.submit(llm.evaluate_prompt, to_send) for llm in self.llms]
      responses     = [future.result().parsed.root for future in futures]
      reponse_types = [type(response).__name__ for response in responses]

      for i, response in enumerate(responses):
        print(f"Response {i}: {response}")

      # If the response contains a dominant activity, return it
      activity = self.find_dominant_activity(responses)

      input(f"dominant activity:{activity}")


  def find_dominant_activity(self, responses: List[Response]) -> Optional[Activity]:

    # If any response is an Ack, that response dominates
    if any(isinstance(response, Ack) for response in responses):
      return Ack(ack="ack")

    # Convert activity in a response into a tuple key
    activity_tup = [response.to_tuple() for response in responses if isinstance(response,Activity)]

    # If there is no activity, return None
    if not activity_tup: return None

    # Count the keys
    activity_counter = Counter(activity_tup)

    # Pull the most common key and its count, and check if it meets our threshold
    (activity_type, processes), count = activity_counter.most_common(1)[0]
    if count < math.ceil(0.75 * len(responses)): return None 

    # Rebuild and return an activity based on that key
    processes = [ProcessQuantity(process=process, quantity=quantity)
                 for process,quantity in processes]
    return Activity(activity_type=activity_type, processes=processes)


  # Aggregates a list of conflicting activities and clarifying questions into a single  
  # clarifying question
  # def generate_clarifying_question(self):










# class Interpreter:

#   def __init__(self, process_status, models, consensus_threshold):
#     self.process_status            = process_status # The global process status
#     self.next_update_id: int       = 0              # Tracks the number of updates
#     self.traces: List[UpdateTrace] = []             # All previous traces

#     self.llms = [ut.LLMInterface(model) for model in models]  # Interpreter LLMs
#     self.consensus_threshold = consensus_threshold

#     with open("prompts/interpreter_prompt3.txt", "r") as file:
#       self.interpreter_prompt = file.read()

#   def main(self) -> None:
#     while True:
#       raw_message = input()
#       self.update(raw_message)

#   def update(self, raw_message) -> None:

#     # Create new trace
#     trace = UpdateTrace(self.next_update_id)
#     trace.trace.append(Message("user", raw_message))
#     self.next_update_id += 1
#     self.traces.append(trace)

#     while True:
#       full_trace = self.build_full_trace()
#       self.print_full_trace(full_trace)
#       responses  = [llm.evaluate_prompt(full_trace) for llm in self.llms]
#       print(f"responses:{responses}")
#       updates    = [Update.from_string(response) for response in responses]
#       print(updates)
#       consensus_update = self.find_consensus()
#       return

#   def build_full_trace(self) -> List[dict]:
#     intepreter_message = Message("system", self.interpreter_prompt).__dict__
#     full_trace         = [message for trace in self.traces for message in trace.augment_trace()]
#     return [intepreter_message] + full_trace

#   def print_full_trace(self, full_trace) -> None:
#     for message in full_trace:
#       print(message)

#   def find_consensus(self, updates: list[Update], consensus_threshold: float) -> Optional[None]:
#     counter = Counter(updates)
#     most_common_update, count = counter.most_common(1)[0]
#     if count / len(updates) >= consensus_threshold:
#       return most_common_update
#     return None




# # The sequence of messages involved in an update conversation
# # id: str. The id associated with the trace.
# # trace: List[Messages]. 
# # update: Optional[Update]. The formal update associated with the conversation.
# class UpdateTrace:
#   def __init__(self, update_id:int):
#     self.id:     int              = update_id # The id associated with the trace
#     self.trace:  List[Messages]   = []        # The trace's sequence of messages.
#     self.update: Optional[Update] = None      # The formal update associated with the trace.

#   def augment_trace(self) -> List[dict]:
#     start_message    = Message("system", f"BEGIN: UPDATE CONVERSATION {self.id}")
#     augemented_trace = [start_message, *self.trace]

#     if self.update:
#       end_message    = Message("assistant", str(self.update))
#       augemented_trace.append(end_message)

#     return [message.__dict__ for message in augemented_trace]


# class Interpreter:

#   def __init__(self, process_status, models, consensus_threshold):
#     self.process_status            = process_status # The global process status
#     self.next_update_id: int       = 0              # Tracks the number of updates
#     self.traces: List[UpdateTrace] = []             # All previous traces

#     self.llms = [ut.LLMInterface(model) for model in models]  # Interpreter LLMs
#     self.consensus_threshold = consensus_threshold

#     with open("prompts/interpreter_prompt3.txt", "r") as file:
#       self.interpreter_prompt = file.read()

#   def main(self) -> None:
#     while True:
#       raw_message = input()
#       self.update(raw_message)

#   def update(self, raw_message) -> None:

#     # Create new trace
#     trace = UpdateTrace(self.next_update_id)
#     trace.trace.append(Message("user", raw_message))
#     self.next_update_id += 1
#     self.traces.append(trace)

#     while True:
#       full_trace = self.build_full_trace()
#       self.print_full_trace(full_trace)
#       responses  = [llm.evaluate_prompt(full_trace) for llm in self.llms]
#       print(f"responses:{responses}")
#       updates    = [Update.from_string(response) for response in responses]
#       print(updates)
#       consensus_update = self.find_consensus()
#       return

#   def build_full_trace(self) -> List[dict]:
#     intepreter_message = Message("system", self.interpreter_prompt).__dict__
#     full_trace         = [message for trace in self.traces for message in trace.augment_trace()]
#     return [intepreter_message] + full_trace

#   def print_full_trace(self, full_trace) -> None:
#     for message in full_trace:
#       print(message)

#   def find_consensus(self, updates: list[Update], consensus_threshold: float) -> Optional[None]:
#     counter = Counter(updates)
#     most_common_update, count = counter.most_common(1)[0]
#     if count / len(updates) >= consensus_threshold:
#       return most_common_update
#     return None