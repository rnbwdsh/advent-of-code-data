import os
from functools import wraps
from os import environ, path

from pychatgpt import Chat

from aocd.models import Puzzle


# an annotation that caches a call to cached_question in a given file format
def file_cached(template):
    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            fn = template.format(**kwargs)
            if not path.exists(fn):
                if out := func(*args, **kwargs):
                    os.makedirs(path.dirname(fn), exist_ok=True)
                    with open(fn, "w") as f:
                        f.write(out)
                    return out
            with open(fn) as f:
                return f.read()

        return wrapper

    return inner


@file_cached(template="example_data/{year}/{day}.txt")
def cached_question(*, year: int, day: int):
    c = Chat(email=environ["EMAIL"], password=environ["PASSWORD"])
    p = Puzzle(year=year, day=day)
    answer = c.ask("""You are given the following assignment. 
Give me the one example of input data and the corresponding output.
Right-trim the input and output.
Write your answer as a json object with the following interface.
Don't comment on it, don't format it. Give me the raw json as an answer.
interface Example {
    input: string;
    output: string|number;
}

""" + p._soup().article.text)
    return answer


for year in range(2015, 2023):
    for day in range(1, 25 if year <= 2022 else 10):
        print(cached_question(year=year, day=day))
