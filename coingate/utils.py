def convert_values(dictionnary, func):
    """
    Recursively converts values in a (possibly nested) ductuinary using a given
    function.
    """
    for k, v in dictionnary.items():
        if isinstance(v, dict):
            convert_values(v, func)
        else:
            dictionnary[k] = func(v)
