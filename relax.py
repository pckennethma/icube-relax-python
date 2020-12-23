import json
from copy import copy
from itertools import product
from util import *
from Cube import Cube

ref_subspace = get_extended_subspace(spec["subspaces"][0],spec["subspaces"][1])
cmp_filter = extract_cmp_filters(spec["subspaces"][0],spec["subspaces"][1])
sibling_subspace = get_sibling_subspaces(ref_subspace, cmp_filter)

# get reference value
val = {i["FILTER"]:i["MEASURE"] for i in get_measure_val_dual(ref_subspace, cmp_filter)}
cmp_col = cmp_filter["col"]
v1 = cmp_filter["val"][0] if cmp_filter["val"][0] != 0 else 0.0000001
v2 = cmp_filter["val"][1] if cmp_filter["val"][1] != 0 else 0.0000001
ref_val_pair = (val[v1], val[v2])

# build cube
cube = Cube(sibling_subspace)
cube.set_val(ref_subspace, ref_val_pair, True)

products = product(*[[(k,i) for i in v+["*"]] for k,v in sibling_subspace.items()])
template_subspace = {k:"*" for k in sibling_subspace}

for p in products:
    for item in p:
        template_subspace[item[0]] = item[1]
    val = {i["FILTER"]:i["MEASURE"] for i in get_measure_val_dual(template_subspace, cmp_filter)}
    v1 = cmp_filter["val"][0]
    v2 = cmp_filter["val"][1]
    if v1 not in val: val[v1] = 0
    if v2 not in val: val[v2] = 0
    curr_val_pair = [val[v1], val[v2]]
    kl = compute_kl_dist_by_val(ref_val_pair, curr_val_pair)
    if kl > spec["threshold"]:
        cube.set_val(template_subspace, curr_val_pair, False)
    else:
        cube.set_val(template_subspace, curr_val_pair, True)

count = 0
merge_col = cube.bottom_up_level2_auto_merge(ref_subspace)
flat_merge_col = []
for col in merge_col:
    if count > spec["topk"]: break
    if isinstance(col, str):
        flat_merge_col.append(col)
        output = ""
        for k,v in ref_subspace.items():
            if k!=col: output += f"{k}: {v}, "
        print(f"For every {col} where {output} the value under {cmp_col}: [{v1}, {v2}] looks similar.")
    else:
        flat_merge_col.append(col[0])
        flat_merge_col.append(col[1])
        output = ""
        for k,v in ref_subspace.items():
            if k not in col: output += f"{k}: {v}, "
        print(f"For every {col[0]} and {col[1]} where {output} the relationship of values under {cmp_col}: {v1} and {v2} looks similar.")
    count += 1


flag = True
products = product(*[[(k,i) for i in v+["*"]] for k,v in sibling_subspace.items()])
for p in products:
    if count > spec["topk"]: break
    for item in p:
        template_subspace[item[0]] = item[1]
    _, is_common = cube.get_val(template_subspace)
    if is_common and not cube.is_subsumed(template_subspace,ref_subspace, flat_merge_col): 
        if flag and len(flat_merge_col) > 0 :
            print("Besides, we also found the following individual entries looks similar.")
            flag = False
        if flag and len(flat_merge_col) == 0:
            print(f"We did not find any similar entries in higher level. Instead, we found the following individual entries looks similar under  {cmp_col}: {v1} and {v2} compared with {ref_subspace}.")
            flag = False
        print(template_subspace)
        count += 1