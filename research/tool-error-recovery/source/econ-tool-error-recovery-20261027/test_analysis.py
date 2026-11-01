import unittest
from analyze import summarize,paired_bootstrap,CONDITIONS

def rows():
 return [dict(task_id=str(i),condition=CONDITIONS[i//10],arm=a,passed=(i%2==0),completed=True) for i in range(40) for a in 'ABC']
class Tests(unittest.TestCase):
 def test_equal(self):
  s=summarize(rows());self.assertEqual(s['pilot_gate']['decision'],'stop_no_qualifying_difference');self.assertEqual(s['strata']['overall']['arms']['A']['assigned'],40)
 def test_one_condition_gate(self):
  r=rows();next(x for x in r if x['task_id']=='1' and x['arm']=='B')['passed']=True
  s=summarize(r);self.assertEqual(s['pilot_gate']['decision'],'eligible_for_main_cost_check');self.assertAlmostEqual(s['strata']['clean']['contrasts'][0]['difference'],.1)
 def test_ceiling_precedes_gate(self):
  r=rows()
  for x in r:x['passed']=True
  r[0]['passed']=False
  self.assertEqual(summarize(r)['pilot_gate']['decision'],'stop_near_ceiling')
 def test_floor(self):
  r=rows()
  for x in r:x['passed']=False
  self.assertEqual(summarize(r)['pilot_gate']['decision'],'stop_near_floor')
 def test_missing_not_failure(self):
  r=rows();r[0]['passed']=None
  s=summarize(r);self.assertEqual(s['strata']['overall']['arms']['A']['missing'],1);self.assertEqual(s['strata']['overall']['arms']['A']['known_failures'],20);self.assertIsNone(s['strata']['overall']['contrasts'][0]['difference'])
 def test_invalid_code_failure_in_denominator(self):
  r=rows();r[0].update(passed=False,completed=False);s=summarize(r);self.assertEqual(s['strata']['overall']['arms']['A']['assigned'],40);self.assertEqual(s['strata']['overall']['arms']['A']['completed'],39)
 def test_no_exposure_filter(self):
  r=rows()
  for x in r:x['realised_erroneous_exposure']=False
  self.assertEqual(summarize(r)['strata']['misleading success']['arms']['A']['assigned'],10)
 def test_bootstrap_pairing(self):
  ci=paired_bootstrap(rows(),'B','A',draws=100);self.assertEqual((ci['lower'],ci['upper']),(0,0))
 def test_duplicate_rejected(self):
  r=rows();r[-1]=r[0]
  with self.assertRaises(ValueError):summarize(r)
if __name__=='__main__':unittest.main()
