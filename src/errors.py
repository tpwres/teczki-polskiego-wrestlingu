class DocError(Exception):
    pass

class ParseError(Exception):
    pass

def format_error(message, filename, line, col):
    if col is not None and line is not None:
        return f"{filename}:{line}:{col} {message}"
    elif line is not None:
        return f"{filename}:{line} {message}"
    else:
        return f"{filename} {message}"
