from copy import copy
import json
from util import *

class Cube:
    def __init__(self, sibling_subspace, measure=spec["measure"]):
        self.measure = measure
        self.empty_subspace = {col:"*" for col in sibling_subspace}
        self.sibling_subspace = sibling_subspace
        self.raw_cube = {}
    
    def set_val(self, subspace, val_pair, is_common):
        cache_key_subspace = copy(self.empty_subspace)
        for col, val in subspace.items():
            assert col in cache_key_subspace
            cache_key_subspace[col] = val
        cache_key_string = json.dumps(cache_key_subspace)
        self.raw_cube[cache_key_string] = (val_pair, is_common)
    
    def get_val(self, subspace):
        cache_key_subspace = copy(self.empty_subspace)
        for col, val in subspace.items():
            assert col in cache_key_subspace
            cache_key_subspace[col] = val
        cache_key_string = json.dumps(cache_key_subspace)
        return self.raw_cube[cache_key_string][0], self.raw_cube[cache_key_string][1]
    
    def bottom_up_level1_auto_merge(self, common_subspace):
        merge_result = []
        for col in common_subspace:
            flag = True
            for val in self.sibling_subspace[col]:
                query_subspace = copy(common_subspace)
                query_subspace[col] = val
                _, is_common = self.get_val(query_subspace)
                if not is_common:
                    flag = False
                    break
            if flag: merge_result.append(col)
        return merge_result
    
    def bottom_up_level2_auto_merge(self, common_subspace):
        level1_merge_result = self.bottom_up_level1_auto_merge(common_subspace)
        merge_result = []
        for col1 in common_subspace:
            if col1 not in level1_merge_result: continue
            for col2 in common_subspace:
                if col1 == col2: continue
                if col2 not in level1_merge_result: continue
                flag = True
                for val1 in self.sibling_subspace[col1]:
                    for val2 in self.sibling_subspace[col2]:
                        query_subspace = copy(common_subspace)
                        query_subspace[col1] = val1
                        query_subspace[col2] = val2
                        _, is_common = self.get_val(query_subspace)
                        if not is_common:
                            flag = False
                            break
                    if not flag: break
                if flag: 
                    level1_merge_result.remove(col1)
                    level1_merge_result.remove(col2)
                    merge_result.append((col1, col2))
        return merge_result + level1_merge_result
    def is_subsumed(self, subspace, ref_subspace, merge_result):
        for k,v in subspace.items():
            if k in merge_result: continue
            if v != ref_subspace[k]: return False
        return True