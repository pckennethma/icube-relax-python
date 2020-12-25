import json, sys, functools, operator
from tqdm import tqdm
from copy import copy
from itertools import product
from util import *
import util
from Cube import Cube
from relax import single_relax

def main(extended_subspaces, target_col, target_pairs, threshold, topk, max_exception):
    count = 0
    context = set()
    for i in product(*[extended_subspaces, target_pairs]):
        if count >= topk: break
        subspace1 = copy(i[0])
        subspace1[target_col] = i[1][0]
        subspace2 = copy(i[0])
        subspace2[target_col] = i[1][1]
        count, context = single_relax(subspace1, subspace2, threshold, topk, count, context, max_exception)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            spec = json.load(f)
            util.spec = spec
    extended_subspaces = get_extended_batched_subspace(spec["auto_cube_batch"])
    if spec["auto_target_batch_type"] == "int-inc":
        target_pairs = get_int_inc_pairs(spec["auto_target_col"])
    else:
        target_pairs = spec["auto_target_pair"]
    main(extended_subspaces, spec["auto_target_col"], target_pairs, spec["threshold"], spec["topk"], spec["max_exception"])