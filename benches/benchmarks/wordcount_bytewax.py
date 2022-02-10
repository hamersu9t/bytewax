import re
import operator

from bytewax import Executor, inp, workers


def tokenize(x):
    x = x.lower()
    return re.findall(r'[^\s!,.?":;0-9]+', x)


def initial_count(word):
    return word, 1


ec = Executor()
flow = ec.Dataflow(inp.single_batch(open("benches/benchmarks/collected-works.txt")))
flow.flat_map(tokenize)
flow.map(initial_count)
flow.reduce_epoch(operator.add)

if __name__ == "__main__":
    workers.start_local_processes(ec, number_of_processes=3)
