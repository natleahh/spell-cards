import getpass
import os

def get_env_variable(variable: str, prompt=False, secret=False):
    try:
        return os.environ[variable]
    except KeyError:
        value_getter = getpass.getpass if secret else input
        if prompt:
            return value_getter(f"Please input {variable}: ")
        raise EnvironmentError(f"No environment variable {variable}")

def word_list(*words: str, sep=",", join="and"):
    match words:
        case [w]:
            return w
        case [a, b]:
            return " ".join([a, join, b])
        case [*ws, a, b]:
            return "{} {}".format(f"{sep} ".join(ws), word_list(a, b, join=join))