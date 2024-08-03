from json import JSONEncoder
from collections import Counter
import re

invalid_names_re = re.compile(r'^([?]+|TBA|Unknown\d*)$')
def accepted_name(name):
    """
    Return false if name is a placeholder, otherwise true.
    """
    return invalid_names_re.match(name) == None

class RichEncoder(JSONEncoder):
    def default(self, o):
        match o:
            case set():
                return list(o)
            case Counter():
                return dict(o)
            case _:
                return super().default(o)
