import lib.utilities as ut
import math
import numpy         as np
import tiktoken

from collections          import Counter
from concurrent.futures   import ThreadPoolExecutor
from enum                 import Enum
from typing               import List, Literal, Optional, Tuple, Union
from pydantic             import BaseModel

# The possible activity types
class ActivityType(Enum):
  SCHEDULE = 1 
  RUN      = 2
  FINISH   = 3

# A message in the trace
class Message:
  def __init__(self, role, content):
    self.role:    str = role
    self.content: str = content

  def __repr__(self):
    return f"{self.role}: {self.content}"

# A class which stores the trace and tracks key information
class Trace:

  def __init__(self, maximum_context_length):

    # A list of messages
    self.trace = []

    # The culmulative token lengths of the messages in the trace. The last message in the trace has 
    # a culmulative token length of tkLen(message[-1]). The second-to-last has culmulative token 
    # length of tkLen(message[-2]) + tkLen(message[-1]) and so on.
    self.culmulative_tokens = []

    # Information to help us compute encoding length
    self.encoding = tiktoken.encoding_for_model("gpt-4o")
    self.tokens_per_message = 4

    # Store the maximum context length. The trace will be truncated so that it is never longer than
    # this length.
    self.maximum_context_length = maximum_context_length

  def store_message(self, message):

    # Add message to trace
    self.trace.append(message)

    # Compute message's token length
    token_len = self.get_token_len(message.content)

    # Update cumulative tokens
    self.culmulative_tokens.append(0)
    self.culmulative_tokens = [prev_len + token_len for prev_len in self.culmulative_tokens]

    self.print_token_len()

  def get_token_len(self, text):
    return len(self.encoding.encode(text)) + self.tokens_per_message

  def format_as_dict(self):
    return [message.__dict__ for message in self.trace]

  def truncated_formatted_trace(self):
    
    # Get the smallest index i such that the messages from message i to the end of the trace 
    # (inclusive) have a cumulative token length of less than self.maximum_context_length
    culmulative_tokens_arr = np.array(self.culmulative_tokens)
    possible_truncation_indices = np.where(culmulative_tokens_arr < self.maximum_context_length)[0]

    assert len(possible_truncation_indices) > 0, \
      "no trace suffix is shorter than the maximum context length"

    min_truncation_index = possible_truncation_indices[0]

    return [message.__dict__ for message in self.trace[min_truncation_index:]]

  def print_trace(self):
    for i, message in enumerate(self.trace):
      print(f"message {i}:{repr(message)}")

  def print_token_len(self):
    for i, message in enumerate(self.trace):
      token_len = self.get_token_len(message.content)
      print((f"message {i}: tk:{token_len} cutk:{self.culmulative_tokens[i]}"))



class Interpreter:

  def __init__(self, models, coordinator, examples_filepath, maximum_context_length):

    ### Dynamically construct typing schema ###

    all_processes     = coordinator.get_all_processes()
    example_processes = list(all_processes)[:2]
    ProcessListEnum   = Enum("ProcessListEnum", {item:item for item in all_processes})

    # An process:item entry 
    class ProcessQuantity(BaseModel):
      process:  ProcessListEnum
      quantity: int

    # When we’ve understood the update, we formalize it
    class Activity(BaseModel):
      activity_type:      ActivityType
      process_quantities: List[ProcessQuantity]

      # Convert this class into a hashable tuple key of the form:
      # (activity_type, ((process, quantity), (process, quantity), ...))
      def to_tuple(self):
        process_quantities_tup = tuple((pq.process, pq.quantity) for pq in self.process_quantities)
        return (self.activity_type, process_quantities_tup)

    # When we need more information, we ask a question
    class Question(BaseModel):
      question: str

    # Top level Response
    class Response(BaseModel):
      root: Union[Activity, Question]

    self.ActivityType    = ActivityType
    self.Activity        = Activity
    self.ProcessQuantity = ProcessQuantity

    # Initialize interpreter
    self.llms           = [ut.LLMInterface(model, Response) for model in models]
    self.question_llm   = ut.LLMInterface("gpt-4o", Question)
    self.trace          = Trace(maximum_context_length)
    self.threshold      = 0.75

    # Load and construct prompts
    with open(examples_filepath, "r") as file:
      examples = file.read()

    with open("prompts/interpreter_prompt4.txt", "r") as file:
      prompt = (file.read().replace("<processes>",        ", ".join(all_processes))
                           .replace("<example_process1>", example_processes[0])
                           .replace("<example_process2>", example_processes[1])
                           .replace("<examples>", examples))

      self.interpreter_prompt = Message("system", prompt)


    with open("prompts/interpreter_infeasible_activity_prompt.txt") as file:
      prompt = (file.read().replace("<processes>",        ", ".join(all_processes))
                           .replace("<example_process1>", example_processes[0])
                           .replace("<example_process2>", example_processes[1]))

      self.infeasible_activity_prompt = Message("system", prompt)

    with open("prompts/interpreter_question_aggregation_prompt.txt") as file:
      prompt = (file.read().replace("<processes>",        ", ".join(all_processes))
                           .replace("<example_process1>", example_processes[0])
                           .replace("<example_process2>", example_processes[1]))

      self.interpreter_question_aggregation_prompt = Message("system", prompt)

    with open("prompts/interpreter_question_aggregation_response_list_prompt.txt") as file:
      self.interpreter_question_aggregation_response_list_prompt = Message("system", file.read())

    # Load user messsage
    self.default_user_msg = "What is your next update?"

    # Initialize workstation state
    self.scheduled = Counter()
    self.running   = Counter()
    self.finished  = Counter()


  def main(self):

    user_msg = self.default_user_msg

    while True:

      # 1) Get reponse from user
      self.trace.print_trace()
      self.get_response_from_user(user_msg)

      # 2) Generate an array of responses to the current trace
      responses = self.interpret_trace()
      self.print_trace_and_responses(responses)
      
      # 3) If the set of responses contains a dominant activity:
      dominant_activity = self.find_dominant_activity(responses)
      if dominant_activity:

        # a) Add the dominant activity to the trace as the assistant's official response
        # b) Check if this activity is feasible, given the current workstation state
        self.trace.store_message(Message("assistant", str(dominant_activity)))
        err_msg = self.check_activity_feasibility_and_update_state(dominant_activity)

        # c) If it isn't feasible, add a message from the system explaining why the activity is
        #    infeasible to the trace. Next, generate a clarifying question for the user.
        if err_msg:
          self.trace.store_message(Message("user", f"system - invalid:{err_msg}"))
          clarifying_question        = self.generate_infeasible_activity_reponse()
          self.trace.store_message(Message("assistant", clarifying_question))
          user_msg = clarifying_question

        # d) Otherwise, add a message confirming that the activity is feasible to the trace and 
        #    update the workstation's state. Next, await the next update from the user
        else:
          feasibility_check_response = f"system - invalid:{err_msg}"
          self.trace.store_message(Message("user", f"system - valid"))
          user_msg = self.default_user_msg
          

      # 4) If the set of responses does not contain a dominant activity, generate a clarifying
      #    question for the user.
      else:
        clarifying_question = self.generate_clarifying_question_response(responses)
        self.trace.store_message(Message("assistant", clarifying_question))
        user_msg = clarifying_question


          
  def get_response_from_user(self, user_msg: str) -> None:
    # from_user = input(f"{user_msg} ")
    from_user = input("> ")
    self.trace.store_message(Message("user", from_user))


  def print_trace_and_responses(self, responses):
    self.trace.print_trace()
    for i, response in enumerate(responses): print(f"Response {i}: {response}")


  def interpret_trace(self):

    with ThreadPoolExecutor(max_workers=len(self.llms)) as executor:

      system_msg = Message("system", self.interpreter_prompt)
      to_send    = [self.interpreter_prompt.__dict__] + self.trace.truncated_formatted_trace()
      futures    = [executor.submit(llm.evaluate_trace, to_send) for llm in self.llms]
      responses  = [future.result().parsed.root for future in futures]

    return responses

      
  def find_dominant_activity(self, responses):

    # Convert each activity specified by a response into a tuple
    activities = [response.to_tuple() for response in responses 
                  if isinstance(response, self.Activity)]

    # If no response specified an activity, return None
    if not activities: return None
    
    # Get the most common activity and its count, and check if it meets our threshold
    activity_counter = Counter(activities)
    (activity_type, process_quantities), count = activity_counter.most_common(1)[0]
    if count < math.ceil(self.threshold * len(responses)): return None 

    # Reconvert the most common activity from a tuple to an Activity
    pq = [self.ProcessQuantity(process=p, quantity=q) for p,q in process_quantities]
    return self.Activity(activity_type=activity_type, process_quantities=pq)


  def generate_infeasible_activity_reponse(self):
    to_send   = [self.infeasible_activity_prompt.__dict__] + self.trace.truncated_formatted_trace()
    response  = self.question_llm.evaluate_trace(to_send)
    return response.parsed.question


  def generate_clarifying_question_response(self, responses):
    response_list_str = self.interpreter_question_aggregation_response_list_prompt.content

    for i, response in enumerate(responses):
      response_list_str += f"Response {i}: {response}\n"


    to_send = (  [self.interpreter_question_aggregation_prompt.__dict__] 
               + self.trace.truncated_formatted_trace() 
               + [Message("user", response_list_str).__dict__])

    response  = self.question_llm.evaluate_trace(to_send)
    # input(f"clarifying question response:{response.parsed.question}")
    return response.parsed.question

