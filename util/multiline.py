from inspect import cleandoc


def unindent(string):
    return cleandoc(string)


def single_line(string):
    return unindent(string).replace("\n", " ")
