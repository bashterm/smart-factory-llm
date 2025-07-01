import lib.utilities as ut
import math
import numpy         as np
import tiktoken

from collections                  import Counter
from concurrent.futures           import ThreadPoolExecutor
from enum                         import Enum
from lib.workstation_interpreter  import ActivityType, Message, Trace
from typing                       import List, Literal, Optional, Tuple, Union
from pydantic                     import BaseModel


class SimpleInterpreter:

  def __init__(self, workstation_id, intepreter_llm_model, question_llm_model, coordinator, 
               examples_filepath, maximum_context_length):

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
    self.id              = workstation_id
    self.interpreter_llm = ut.LLMInterface(intepreter_llm_model, Response)
    self.question_llm    = ut.LLMInterface(question_llm_model,   Question)
    self.trace           = Trace(maximum_context_length)

    # Store a handle to the coordinator
    self.coordinator     = coordinator

    # Load and construct prompt
    with open(examples_filepath, "r") as file:
      examples = file.read()

    with open("prompts/interpreter_prompt3.txt", "r") as file:

      prompt = (file.read().replace("<processes>",        ", ".join(all_processes))
                           .replace("<example_process1>", example_processes[0])
                           .replace("<example_process2>", example_processes[1])
                           .replace("<examples>", examples))

      self.interpreter_prompt = Message("system", prompt)

      # input(f"self.interpreter_prompt:{self.interpreter_prompt}")

  def main(self):

    while True:

      # 1) Get reponse from user
      self.trace.print_trace()
      self.get_response_from_user()

      # 2) Generate an response to the current trace
      response = self.interpret_trace()
      self.print_trace_and_response(response)

      # 3) If the reponse is an activity: 
      #    a) Add it to the trace
      #    b) Check if it is feasible, given the current workstation state
      #    c) If it is feasible, add the feasibility message to the trace and await the next 
      #       update message from the user.
      #    d) If it is not feasible, generate a clarifying question for the user
      if isinstance(response, self.Activity):
        self.trace.store_message(Message("assistant", str(response)))
        err_msg = self.coordinator.check_activity_feasibility_and_update_state(self.id, response)

        if err_msg:
          self.trace.store_message(Message("user", f"system - invalid:{err_msg}"))
          clarifying_question = self.interpret_trace()
          self.trace.store_message(Message("assistant", clarifying_question.question))

        else:
          self.trace.store_message(Message("user", f"system - valid"))

      # 4) If the response is a question, add it to the trace and await the next message from the
      #    user.
      else:
        self.trace.store_message(Message("user", response.question))

          
  def get_response_from_user(self):
    from_user = input("> ")
    self.trace.store_message(Message("user", from_user))


  def print_trace_and_response(self, response):
    self.trace.print_trace()
    print(f"Response: {response}")


  def interpret_trace(self):
    system_msg = Message("system", self.interpreter_prompt)
    to_send    = [self.interpreter_prompt.__dict__] + self.trace.truncated_formatted_trace()
    response   = self.interpreter_llm.evaluate_trace(to_send).parsed.root
    return response