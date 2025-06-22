import matplotlib.pyplot   as     plt

from   collections         import namedtuple
from   concurrent.futures  import ThreadPoolExecutor
from   matplotlib          import transforms
from   openai              import OpenAI
from   typing              import List


class Pt:
  
  def __init__(self, x, y):
    self.x = x
    self.y = y

  def add(self, cell):
    return Pt(self.x + cell.x, self.y + cell.y)

  def avg(self, cell):
    point_sum = self.add(cell)
    return Pt(point_sum.x/2, point_sum.y/2)

  def to_tuple(self):
    return (self.x, self.y)

  def __eq__(self, cell):
    return self.x == cell.x and self.y == cell.y

  def __repr__(self):
    return f"({self.x},{self.y})"


# Cardinal directions
directions          = ["n",  "e",  "w",  "s"]
direction_to_v      = {"n":Pt(0,1), "e":Pt(1,0), "w":Pt(-1,0), "s":Pt(0,-1)}

# is_adjacent : Checks if coord u is adjacent to coord v
def is_adjacent(u, v):
  return any(u.add(dir_to_vec[direction]) == v for direction in dir_to_vec)

# Convert string to cell
def to_cell(s):
  tokens = s.split(",")
  return Pt(int(tokens[0]), int(tokens[1]))
  
# Takes two adjacent cells u and v. Returns the direction that you have to travel from u to
# get to v. If u and v are not adjacent, throw error
def direction_of_v_from_u(u, v):

  for direction, direction_v in direction_to_v.items():
    if u.add(direction_v) == v:
      return direction

  raise RuntimeError(f"get_direction: pts {u} and {v} are not adjacent.")



# Draw rainbow text
def rainbow_text(x, y, ls, lc, fig, t, **kw):
  for s,c in zip(ls,lc):
    text = plt.text(x,y,s+" ",color=c, transform=t, **kw)
    text.draw(fig.canvas.get_renderer())
    ex = text.get_window_extent()
    t = transforms.offset_copy(text._transform, x=ex.width, units='dots')


# A message in a trace
class Message:
  def __init__(self, role, content):
    self.role:    str = role
    self.content: str = content

  def __repr__(self):
    return f"{self.role}: {self.content}"


# Interface to an LLM
class LLMInterface:

  def __init__(self, model, response_format):
    self.client          = OpenAI()
    self.model           = model
    self.response_format = response_format

  # evaluate_trace: asks the client LLM to evaluate a trace
  def evaluate_trace(self, trace):
    completion  = self.client.beta.chat.completions.parse(
      model           = self.model,
      messages        = trace,
      response_format = self.response_format)

    return completion.choices[0].message


# Interface to an ensemble of LLMs
class EnsembleInterface:

  def __init__(self, models, response_format):
    self.llms = [LLMInterface(model, response_format) for model in models]

  def evaluate_traces(self, traces):
    with ThreadPoolExecutor(max_workers=len(self.llms)) as executor:
      futures   = [executor.submit(llm.evaluate_trace, trace) 
                   for llm, trace in zip(self.llms, traces)]
      responses = [future.result() for future in futures]
      return responses


# Interface to an ensemble of LLMs
class ScalingEnsembleInterface:

  def __init__(self, model, response_format):
    self.model           = model
    self.response_format = response_format

  def evaluate_traces(self, id_to_trace):
    
    id_to_llm = {trace_id: LLMInterface(self.model, self.response_format) 
                 for trace_id in id_to_trace}

    with ThreadPoolExecutor(max_workers=len(id_to_llm)) as executor:

      id_to_future   = {trace_id : executor.submit(llm.evaluate_trace, id_to_trace[trace_id]) 
                        for trace_id, llm in id_to_llm.items()}

      id_to_response = {trace_id : future.result() for trace_id, future in id_to_future.items()}

      return id_to_response




colors = ['deepskyblue', 'salmon', 'cyan', 'dodgerblue', 'yellow','sandybrown', 
          'azure', 'violet', 'darkseagreen', 'chocolate', 'magenta',
             'indigo', 'mediumvioletred', 'darkgray', 'coral', 'papayawhip', 'moccasin', 
             'mediumaquamarine', 'grey', 'mediumblue', 'seashell', 'darksalmon', 'limegreen', 
            'darkslategray', 'tomato', 'lemonchiffon', 'saddlebrown', 'aqua', 'brown', 'turquoise', 
            'thistle', 'greenyellow', 'honeydew', 'black', 'darkcyan', 'lightsalmon', 'bisque', 
            'mediumspringgreen', 'cornsilk', 'orchid', 'navajowhite', 'gainsboro', 'silver', 
            'palegoldenrod', 'mediumseagreen', 'lightseagreen', 'peru', 'royalblue', 'floralwhite', 
            'beige', 'darkorchid', 'darkolivegreen', 'yellowgreen', 'blanchedalmond', 'slategray', 
            'deeppink', 'mediumturquoise', 'sienna', 'lightgray', 'springgreen', 
            'lightcoral', 'palegreen', 'powderblue', 'lightgoldenrodyellow', 'aquamarine', 'plum', 
            'wheat', 'mistyrose', 'lightgrey', 'slategrey', 'navy', 'darkgoldenrod', 'forestgreen', 
            'fuchsia', 'crimson', 'darkviolet', 'teal', 'gold', 'darkred', 'darkgreen', 
            'lawngreen', 'mediumpurple', 'lightgreen', 'pink', 'whitesmoke', 'lavender', 
            'lightcyan', 'orange', 'blue', 'steelblue', 'hotpink', 'tan', 'peachpuff', 'red', 
            'rosybrown', 'gray', 'snow', 'purple', 'aliceblue', 'maroon', 'cornflowerblue', 
            'darkorange', 'indianred', 'lavenderblush', 'palevioletred', 'cadetblue', 'lime', 
            'lightyellow', 'skyblue', 'lightsteelblue', 'darkturquoise', 'darkslateblue', 
            'paleturquoise', 'mediumslateblue', 'olive', 'linen', 'lightblue', 'lightskyblue', 
            'orangered', 'goldenrod', 'olivedrab', 'darkmagenta', 'antiquewhite', 'slateblue', 
            'chartreuse', 'darkblue', 'lightslategrey', 'ghostwhite', 'mintcream', 'seagreen', 
            'white', 'khaki', 'darkkhaki', 'firebrick', 'midnightblue', 'blueviolet', 
            'indigo', 'mediumvioletred', 'darkgray', 'coral', 'papayawhip', 'moccasin', 
            'lightpink', 'darkslategrey', 'rebeccapurple', 'burlywood', 'oldlace', 'mediumorchid',
            'green', 'dimgray', 'dimgrey']


# The color of the null product
NULL_COLOR  = "#777777"