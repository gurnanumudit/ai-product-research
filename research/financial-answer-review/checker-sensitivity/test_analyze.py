"""Synthetic-only tests; no study-response access."""
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import analyze as a
from package.checker import CheckReport
from package.policies import PolicyDecision


def payload(answer='1.002', unit='percent'):
    return {'answer':answer,'unit':unit,'scale':'1','confidence':.5,
            'operands':[{'id':'o1','value':'1','location_id':'table','quote':'1'}],
            'constants':[],'expression':'o1'}


class Synthetic(unittest.TestCase):
    def test_percent_fraction_adapter(self):
        r = a.residual_scale(payload('1.005'), {'exe_ans':.01,'program':'divide(1,100)'})
        self.assertEqual(r, Fraction('.005'))

    def test_percent_point_adapter(self):
        r = a.residual_scale(payload('1.005'), {'exe_ans':1,'program':'multiply(#0, const_100)'})
        self.assertEqual(r, Fraction('.005'))

    def test_ratio_adapter(self):
        r = a.residual_scale(payload('1.00005','ratio'), {'exe_ans':1,'program':'add(1,0)'})
        self.assertEqual(r, Fraction('.005'))

    def test_money_adapter_no_scale_repair(self):
        p = payload('1.005','USD'); p['scale']='1000000'
        self.assertEqual(a.residual_scale(p, {'exe_ans':1,'program':'add(1,0)'}),Fraction('.005'))

    def test_inclusive_boundary(self):
        self.assertEqual(a.label_at(Fraction('.005'),Fraction('.005')),'match')
        self.assertEqual(a.label_at(Fraction('.0050001'),Fraction('.005')),'numeric_nonmatch')

    def test_exact_is_not_strict_round5(self):
        p=payload('1.000001','USD'); ref={'exe_ans':1,'program':'add(1,0)'}
        self.assertEqual(a.old.score(p,ref,strict=True),'match')
        self.assertEqual(a.label_at(a.residual_scale(p,ref),Fraction(0)),'numeric_nonmatch')

    def test_null_remains_abstention(self):
        self.assertEqual(a.label_at(None,Fraction('.01')),'abstention')

    def test_checker_preserves_other_warnings(self):
        original=CheckReport('a',True,.5,('arithmetic','evidence','unused'),details=('arithmetic_mismatch','unknown_location:o1','unused_declared_inputs'))
        modified,residual=a.adjusted_checker(payload(),original)
        self.assertEqual(modified.warnings,('evidence','unused'))
        self.assertEqual(residual,Fraction('.002'))
        self.assertNotIn('arithmetic_mismatch',modified.details)
        self.assertIn('unknown_location:o1',modified.details)

    def test_checker_ratio_boundary(self):
        r=CheckReport('a',True,.5,('arithmetic',))
        self.assertEqual(a.adjusted_checker(payload('1.00005','ratio'),r)[0].warnings,())
        self.assertEqual(a.adjusted_checker(payload('1.000051','ratio'),r)[0].warnings,('arithmetic',))

    def test_checker_unusable_untouched(self):
        r=CheckReport('a',False,None,mandatory_reasons=('unusable',))
        self.assertEqual(a.adjusted_checker({},r),(r,None))

    def test_threshold_does_not_read_gold(self):
        r=CheckReport('a',True,.5,('arithmetic',))
        with patch.object(a,'residual_scale',side_effect=AssertionError('gold access')):
            a.adjusted_checker(payload(),r)

    def test_multiple_sign_changes_and_endpoint(self):
        def d(ids):return PolicyDecision('',True,2,(),tuple(ids),(), '')
        residuals={'a':Fraction('.001'),'b':Fraction('.004'),'c':Fraction('.002'),'d':Fraction('.003')}
        result=a.breakpoint_intervals(residuals,{5:{'confidence':d(['a','b']),'verification_priority':d(['c','d'])}})['5']
        self.assertEqual([r['sign'] for r in result['sign_intervals']],['tie','verification','tie','confidence','tie'])
        self.assertTrue(result['nonmonotonic_delta'])
        self.assertTrue(result['steps'][-1]['right_inclusive'])

    def test_refuse_existing_and_source_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); archive=root/'archive'; archive.mkdir()
            with self.assertRaises(ValueError):a.old.fresh_destination(archive,archive)
            with self.assertRaises(ValueError):a.old.fresh_destination(archive/'new',archive)

    def test_svg_has_zero_line_and_label(self):
        def d(ids):return PolicyDecision('',True,1,(),tuple(ids),(), '')
        chart=a.difference_chart(a.breakpoint_intervals({'a':Fraction('.001'),'b':Fraction('.002')},{5:{'confidence':d(['a']),'verification_priority':d(['b'])}}))
        self.assertIn('+0',chart)
        self.assertIn('ratio: t/100',chart)


if __name__=='__main__':
    unittest.main()
