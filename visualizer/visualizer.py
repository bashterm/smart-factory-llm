import json

def main(config_path):

  ### Load Config
  with open(config_path) as file:
    config = json.loads(file.read())

  ### Load Plan
  with open(config["plan_path"]) as file:
    plan = json.loads(file.read())

  ### Map tokens to colors and symbols
  with open(config["procedure_path"]) as file:
    procedure       = json.loads(file.read())
    token_to_color  = {token:token_colors[ii] for ii, token in enumerate(procedure["tokens"])}
    token_to_color['empty'] = 'darkgrey'
    token_to_symbol = {token:token[0] for token in procedure["tokens"]}
    token_to_symbol['empty'] = "ℰ"

  ### Generate states
  states = {}
  for t in range(plan["timesteps"]):
    states[t] = {"assignment":      plan["assignment"],
                 "rate":            plan["rate"],
                 "plan":            plan["plan"][str(t)],
                 "token_to_color":  token_to_color,
                 "token_to_symbol": token_to_symbol,
                 "timesteps":       plan["timesteps"]}

  ### Display plan
  t     = 0
  delay = "manual"

  while True:

    ### Delay before visualizing next timestep
    display_text = f"> Show factory at timestep {t}?"
    if delay == "manual":
      input(display_text) 
    else:
      print(display_text)

    ### Output state
    with open(config["vis_state"], 'w') as file:
      json.dump(states[t], file)

    ### Advance timestep
    t = (t + 1) % plan["timesteps"]



# The names of the products in the warehouse
token_colors = ['lightcoral', 'palegreen', 'powderblue', 'lightgoldenrodyellow', 'aquamarine', 'plum', 
                'wheat', 'mistyrose', 'lightgrey', 'slategrey', 'navy', 'darkgoldenrod', 'forestgreen', 
                'fuchsia', 'crimson', 'darkviolet', 'teal', 'gold', 'darkred', 'darkgreen', 
                'deepskyblue', 'salmon', 'cyan', 'dodgerblue', 'yellow', 'darkgrey', 'sandybrown', 
                'lawngreen', 'mediumpurple', 'lightgreen', 'pink', 'whitesmoke', 'lavender', 
                'lightcyan', 'orange', 'blue', 'steelblue', 'hotpink', 'tan', 'peachpuff', 'red', 
                'rosybrown', 'gray', 'snow', 'purple', 'aliceblue', 'maroon', 'cornflowerblue', 
                'darkorange', 'indianred', 'lavenderblush', 'palevioletred', 'cadetblue', 'lime', 
                'lightyellow', 'skyblue', 'lightsteelblue', 'darkturquoise', 'darkslateblue', 
                'paleturquoise', 'mediumslateblue', 'olive', 'linen', 'lightblue', 'lightskyblue', 
                'orangered', 'goldenrod', 'olivedrab', 'darkmagenta', 'antiquewhite', 'slateblue', 
                'chartreuse', 'darkblue', 'lightslategrey', 'ghostwhite', 'mintcream', 'seagreen', 
                'indigo', 'mediumvioletred', 'darkgray', 'coral', 'papayawhip', 'moccasin', 
                'lightpink', 'darkslategrey', 'rebeccapurple', 'burlywood', 'oldlace', 'mediumorchid', 
                'azure', 'violet', 'darkseagreen', 'chocolate', 'lightslategray', 'magenta', 'ivory', 
                'white', 'khaki', 'darkkhaki', 'firebrick', 'midnightblue', 'blueviolet', 
                'darkslategray', 'tomato', 'lemonchiffon', 'saddlebrown', 'aqua', 'brown', 'turquoise', 
                'thistle', 'greenyellow', 'honeydew', 'black', 'darkcyan', 'lightsalmon', 'bisque', 
                'mediumspringgreen', 'cornsilk', 'orchid', 'navajowhite', 'gainsboro', 'silver', 
                'palegoldenrod', 'mediumseagreen', 'lightseagreen', 'peru', 'royalblue', 'floralwhite', 
                'beige', 'darkorchid', 'darkolivegreen', 'yellowgreen', 'blanchedalmond', 'slategray', 
                'deeppink', 'mediumturquoise', 'sienna', 'lightgray', 'springgreen', 
                'mediumaquamarine', 'grey', 'mediumblue', 'seashell', 'darksalmon', 'limegreen', 
                'green', 'dimgray', 'dimgrey']


if __name__ == "__main__":
  main("config/simple_factory.json")