import copy
import unittest
import reproduce as r
from analysis import analyze, ratio

class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.rows=r.read('data/outcomes.json');self.schedule=r.read('data/schedule.json')
        self.missing=r.read('data/missing-keys.json');self.costs=r.read('data/interrupted-costs.json')
    def validate(self):return r.validate_inputs(self.rows,self.schedule,self.missing,self.costs)
    def test_full_replay(self):r.reproduce()
    def test_duplicate_outcome_rejected(self):
        self.rows[1]=copy.deepcopy(self.rows[0])
        with self.assertRaises(ValueError):self.validate()
    def test_missing_replacement_rejected(self):
        self.missing[0]=self.rows[0]['key']
        with self.assertRaises(ValueError):self.validate()
    def test_changed_assignment_rejected(self):
        self.rows[0]['role_features']=[999,998]
        with self.assertRaises(ValueError):self.validate()
    def test_bad_credit_rejected(self):
        pairs=self.validate();self.rows[0]['features_credit']=3
        with self.assertRaises(ValueError):analyze(self.rows,pairs,interrupted_costs=self.costs)
    def test_aborted_cost_not_dropped(self):
        self.costs['SIMPLE']['settled_nano_usd']=0
        with self.assertRaises(ValueError):self.validate()
    def test_zero_success_ratio_undefined(self):self.assertIsNone(ratio(1,0))

if __name__=='__main__':unittest.main()
