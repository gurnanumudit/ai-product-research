import ast,unittest
from pathlib import Path
from analyze import summarize,paired_bootstrap,CONDITIONS

def rows():
 return [dict(task_id=str(i),condition=CONDITIONS[i//60],arm=a,passed=(i%2==0),completed=True) for i in range(240) for a in 'ABC']
class Tests(unittest.TestCase):
 def test_frozen_pure_stats_source_identical(self):
  here=Path(__file__).resolve().parent
  def functions(p):
   text=p.read_text();return {n.name:ast.get_source_segment(text,n) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
  a=functions(here/'analyze.py');b=functions(here.parent/'econ-tool-error-recovery-20261027'/'analyze.py')
  for n in ('metrics','contrast','paired_bootstrap'):self.assertEqual(a[n],b[n],n)
 def test_all_assigned_no_gate(self):
  s=summarize(rows());self.assertEqual(s['assigned_arms'],720);self.assertNotIn('pilot_gate',s);self.assertFalse(s['further_study_authorized']);self.assertEqual(s['strata']['overall']['arms']['A']['assigned'],240)
 def test_all15_bootstrap_20000_visible_data(self):
  r=rows()
  for x in r:x['passed']=x['arm']!='A'
  s=summarize(r,bootstrap=True);pairs=[v for t in s['strata'].values() for v in t['contrasts']]
  self.assertEqual(len(pairs),15)
  for v in pairs:
   self.assertEqual(v['bootstrap95']['draws'],20000)
   expected=0 if v['contrast']=='C-B' else 1
   self.assertEqual((v['bootstrap95']['lower'],v['bootstrap95']['upper']),(expected,expected))
 def test_ceiling_floor_do_not_create_new_study_gate(self):
  for value in (True,False):
   r=rows()
   for x in r:x['passed']=value
   s=summarize(r);self.assertNotIn('pilot_gate',s);self.assertFalse(s['further_study_authorized'])
 def test_missing_no_imputation(self):
  r=rows();r[0]['passed']=None;s=summarize(r,bootstrap=True)
  a=s['strata']['overall']['arms']['A'];self.assertEqual(a['missing'],1);self.assertEqual(a['known_failures'],120);self.assertAlmostEqual(a['success_lower'],119/240);self.assertAlmostEqual(a['success_upper'],.5)
  v=s['strata']['overall']['contrasts'][0];self.assertIsNone(v['difference']);self.assertIsNone(v['bootstrap95']);self.assertEqual(v['assigned_pairs'],240)
 def test_no_exposed_filter_and_invalid_code_denominator(self):
  r=rows()
  for x in r:x.update(realised_erroneous_exposure=False)
  r[0].update(passed=False,completed=False);s=summarize(r)
  self.assertEqual(s['strata']['misleading success']['arms']['A']['assigned'],60);self.assertEqual(s['strata']['overall']['arms']['A']['completed'],239)
 def test_paired_bootstrap_equal(self):
  c=paired_bootstrap(rows(),'B','A',draws=100);self.assertEqual((c['lower'],c['upper']),(0,0))
 def test_duplicate_rejected(self):
  r=rows();r[-1]=r[0]
  with self.assertRaises(ValueError):summarize(r)
if __name__=='__main__':unittest.main()
