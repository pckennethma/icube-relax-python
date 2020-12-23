import pymysql
import json
import numpy as np
from scipy.special import kl_div
from itertools import product

with open("spec.json") as f:
    spec = json.load(f)

query_cache = {}

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_db():
    return pymysql.connect(spec["hostname"],spec["username"], spec["passwd"], spec["database"])

def get_measure_val_single(subspace, debug=False):
    db = get_db()
    query =  "SELECT " + spec["measure"] + " AS MEASURE "
    query += "FROM " + spec["table"] + " WHERE "
    cond = [f"{k}='{v}'" for k, v in subspace.items() if v != "*"]
    query += " AND ".join(cond)
    if debug: print(query)
    cursor = db.cursor()
    cursor.execute(query)
    db.close()
    val = cursor.fetchone()
    return val[0]

def get_extended_subspace(subspace1, subspace2):
    assert len(subspace1) == len(subspace2)
    ext_subspace = {}
    for k, v in subspace1.items():
        if v == subspace2[k]:
            ext_subspace[k] = v
    return ext_subspace

def extract_cmp_filters(subspace1, subspace2):
    assert len(subspace1) == len(subspace2)
    cmp_filter = {"col":"", "val": []}
    for k, v in subspace1.items():
        if v != subspace2[k]:
            cmp_filter["col"] = k
            cmp_filter["val"] = [v, subspace2[k]]
            return cmp_filter
    return None

def get_measure_val_dual(subspace, cmp_filter, debug=False):
    cmp_col = cmp_filter["col"] 
    assert cmp_col not in subspace

    db = get_db()
    query =  "SELECT " + spec["measure"] + " AS MEASURE, "
    query +=  cmp_filter["col"] + " AS FILTER "
    query += "FROM " + spec["table"] + " WHERE "
    cond = [f"{k}='{v}'" for k, v in subspace.items() if v != "*"]
    v1 = cmp_filter["val"][0]
    v2 = cmp_filter["val"][1]
    filter_cond = f"({cmp_col}='{v1}' OR {cmp_col}='{v2}')"
    cond.append(filter_cond)
    query += " AND ".join(cond)
    query += " GROUP BY " + cmp_col

    if debug: print(query)
    if query in query_cache:
        val = query_cache[query]
    else:
        cursor = db.cursor(pymysql.cursors.DictCursor)
        cursor.execute(query)
        db.close()
        val = cursor.fetchall()
        query_cache[query] = val
    return val

def get_sibling_subspaces(subspace, cmp_filter={"col":"placeholder"}, debug=False):
    cmp_col = cmp_filter["col"] 
    assert cmp_col not in subspace
    sibling_subspace = {}

    db = get_db()
    for col in subspace:
        query =  f"SELECT DISTINCT {col} AS COL "
        query += "FROM " + spec["table"]
        if debug: print(query)
        if query in query_cache:
            val = query_cache[query]
        else:
            cursor = db.cursor()
            cursor.execute(query)
            val = cursor.fetchall()
            query_cache[query] = val
        sibling_subspace[col] = [v[0] for v in val]
    db.close()
    return sibling_subspace

def compute_kl_dist(ref_subspace, new_subspace, cmp_filter):
    cmp_col = cmp_filter["col"] 
    v1 = cmp_filter["val"][0]
    v2 = cmp_filter["val"][1]
    assert cmp_col not in ref_subspace and cmp_col not in new_subspace

    raw_ref = {i["FILTER"]: i["MEASURE"] for i in get_measure_val_dual(ref_subspace, cmp_filter)}
    raw_new = {i["FILTER"]: i["MEASURE"] for i in get_measure_val_dual(new_subspace, cmp_filter)}
    if v1 not in raw_ref or raw_ref[v1] == 0:
        raw_ref[v1] = 0.0000001
    if v1 not in raw_new or raw_new[v1] == 0:
        raw_new[v1] = 0.0000001
    if v2 not in raw_ref or raw_ref[v2] == 0:
        raw_ref[v2] = 0.0000001
    if v2 not in raw_new or raw_new[v2] == 0:
        raw_new[v2] = 0.0000001
    
    P = np.array([raw_ref[v1], raw_ref[v2]]) 
    P = P/P.sum()
    Q = np.array([raw_new[v1], raw_new[v2]])
    Q = Q/Q.sum()
    return np.sum(kl_div(P, Q))

# get the incremental pairs of int columns (e.g., 1990 vs. 1991, 1991 vs. 1992, ...)
def get_int_inc_pairs(auto_target_col):
    db = get_db()
    query = f"SELECT distinct convert({auto_target_col}, UNSIGNED INTEGER) as TARGET FROM " + spec["table"] + " ORDER BY TARGET ASC"
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute(query)
    db.close()
    val = [i["TARGET"] for i in cursor.fetchall()]
    pairs = []
    for i in range(len(val)-1):
        pairs.append((str(val[i]), str(val[i+1])))
    return pairs


def compute_kl_dist_by_val(ref, new):
    ref = np.array(ref)
    if ref[0]==0: ref[0] = 0.0000001
    if ref[1]==0: ref[1] = 0.0000001
    if new[0]==0: new[0] = 0.0000001
    if new[1]==0: new[1] = 0.0000001
    if sum(ref) == 0 or sum(new) == 0: return float("inf")
    P = np.array(ref) 
    P = P/P.sum()
    Q = np.array(new)
    Q = Q/Q.sum()
    return np.sum(kl_div(P, Q))

def get_extended_batched_subspace(cube_batch):
    prod_list = []
    ext_subspaces = []
    for k, v in cube_batch.items():
        l = []
        if v == "ALL":
            siblings = get_sibling_subspaces({k:""})[k]
            for val in siblings:
                l.append((k,val))
        else:
            for val in v:
                l.append((k,val))
        prod_list.append(l)
    for p in product(*prod_list):
        ext_subspaces.append({i[0]:i[1] for i in p})
    return ext_subspaces


if __name__ == "__main__":
    from copy import copy
    ref_subspace = get_extended_subspace(spec["subspaces"][0],spec["subspaces"][1])
    new_subspace = copy(ref_subspace)
    new_subspace["ENERGY_SOURCE"] = "Wood and Wood Derived Fuels"
    cmp_filter = extract_cmp_filters(spec["subspaces"][0],spec["subspaces"][1])
    print(compute_kl_dist(ref_subspace, new_subspace, cmp_filter)) 