import unittest
from actual_report import secondary_metrics
class Tests(unittest.TestCase):
 def row(self,passed=False,complete=True):
  return dict(passed=passed,completion='complete' if complete else 'incomplete',final_code_present=False,final_code_syntactically_valid=None,calls=4,revisions=0,explicit_reruns=0,automatic_verifications=0,evaluator_count=0,evaluator_seconds=0,invalid_outputs=4,first_actual_passed=None,first_report_differs=None,first_verdict_differs=None)
 def test_terminal_is_not_syntax(self):
  s=secondary_metrics([self.row() for _ in range(40)],{});self.assertEqual(s['terminal_complete'],40);self.assertEqual(s['syntax_valid'],0)
 def test_missing_outcome_efficiency_upper(self):
  rr=[self.row() for _ in range(40)];rr[0]['passed']=True;rr[1]=self.row(None,False)
  s=secondary_metrics(rr,dict(settled_nano_usd=10**9,pending_nano_usd=50_000_000));self.assertEqual(s['success_per_api_usd_upper'],2);self.assertAlmostEqual(s['success_per_api_usd_lower'],1/1.05)
 def test_zero_cost_not_zero_yield(self):
  s=secondary_metrics([self.row(None,False) for _ in range(40)],{});self.assertIsNone(s['success_per_api_usd_upper']);self.assertEqual(s['efficiency_zero_settled_denominator'],'unbounded_or_undefined')
if __name__=='__main__':unittest.main()
