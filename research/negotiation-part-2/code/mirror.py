"""Exact scenario reflection from the frozen preparation code."""
import copy
def mirror(s):
    result = copy.deepcopy(s)
    for new, old in [('buyer', 'seller'), ('seller', 'buyer')]:
        p = s[old]
        result[new] = dict(base=260-p['base']-sum(p['marginals']),
                           marginals=p['marginals'][:], outside_option=p['outside_option'])
    return result
