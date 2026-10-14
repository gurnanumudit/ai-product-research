"""Independent deterministic checks; no RNG, cohort sweep or file writes."""

from fractions import Fraction as F
import itertools
import math
import statistics
import unittest

import simulation as prod
import summarize as report


class IndependentReviewTests(unittest.TestCase):
    def test_exact_context_law_by_enumeration(self):
        # Independent exhaustive m=2 law, not production probability helpers.
        for delta, h in itertools.product((F(-1,25), F(1,50), F(1,10)), (F(0), F(3,10))):
            total = mean = second = cross = F(0)
            for c, ds in itertools.product((-1,1), itertools.product((-1,0,1), repeat=2)):
                mass = F(1,2)
                for d in ds:
                    mass *= { -1:(F(1,2)-delta-h*c)/2,
                              0:F(1,2), 1:(F(1,2)+delta+h*c)/2 }[d]
                D = F(sum(ds),2)
                total += mass
                mean += mass*D
                second += mass*D*D
                cross += mass*ds[0]*ds[1]
            actual = prod.law(F(1,2),delta,h,2)
            self.assertEqual(total,1)
            self.assertEqual(mean,delta)
            self.assertEqual(actual['mean_D'],mean)
            self.assertEqual(actual['variance_D'],second-mean*mean)
            self.assertEqual(actual['covariance_d'],cross-delta*delta)

    def test_interval_matches_separate_statistics_reference(self):
        values = [-1,0,1,.2,.6,-.4,.8,0] * 5
        for k,z in ((1,1.959963984540054),(5,2.5758293035489004)):
            result = prod.normal_interval(values,looks_adjustment=k)
            mean = statistics.fmean(values)
            se = statistics.stdev(values)/math.sqrt(len(values))
            self.assertAlmostEqual(result['mean'],mean,places=13)
            self.assertAlmostEqual(result['se'],se,places=13)
            self.assertAlmostEqual(result['lower'],mean-z*se,places=13)
            self.assertAlmostEqual(result['upper'],mean+z*se,places=13)

    def test_float_identical_vector_is_degenerate(self):
        for count in (3,39,40,199,200):
            result = prod.normal_interval([.2]*count)
            self.assertEqual(result['reason'],'zero_sd')
            self.assertIsNone(result['lower'])
            self.assertEqual(prod.interval_decision(result),'inconclusive')

    def test_strict_threshold_and_truth_equality(self):
        self.assertEqual(prod.interval_decision({'lower':.02,'upper':.4,'reason':None}),'inconclusive')
        self.assertEqual(prod.interval_decision({'lower':-.4,'upper':.02,'reason':None}),'inconclusive')
        self.assertEqual(prod.classify('ship',.02),'false_ship')
        self.assertEqual(prod.classify('hold',.02),'correct_hold')
        self.assertEqual(prod.classify('hold',.10),'false_hold')

    def test_first_decision_precedes_later_fault_and_reversal(self):
        rows = [prod.ObservedRow(i,0,i%2,i) for i in range(40)]
        rows += [prod.ObservedRow(i,1,0,i) for i in range(40,200) if i != 190]
        result = prod.evaluate_cohort(rows,m=1)
        for method in ('row_peek','context_peek','context_adjusted','integrity_adjusted'):
            self.assertEqual(result['methods'][method]['decision'],'ship')
            self.assertEqual(result['methods'][method]['decision_contexts'],40)
        self.assertEqual(result['methods']['row_fixed']['decision'],'hold')
        self.assertEqual(result['looks'][-1]['intervals']['integrity_adjusted']['reason'],'integrity_missing_pairs')

    def test_zero_is_not_missing_and_identical_duplicate_is_recoverable(self):
        rows = [prod.ObservedRow(i,i%2,0,i//5) for i in range(20)]
        rows.append(rows[0])
        full = prod.evaluate_prefix(rows,4,m=5)
        self.assertIsNone(full['diagnostics']['integrity_reason'])
        self.assertEqual(full['diagnostics']['duplicate_extra_rows'],1)
        self.assertEqual(full['intervals']['integrity_adjusted']['mean'],-.5)
        missing = prod.evaluate_prefix(rows[1:],4,m=5)  # Duplicate still supplies pair 0.
        self.assertIsNone(missing['diagnostics']['integrity_reason'])
        missing = prod.evaluate_prefix(rows[1:-1],4,m=5)
        self.assertEqual(missing['diagnostics']['missing_pairs'],1)
        self.assertEqual(missing['decisions']['integrity_adjusted'],'inconclusive')

    def test_conflicting_duplicate_is_not_silently_cleaned(self):
        rows = [prod.ObservedRow(i,0,i%2,i//5) for i in range(20)]
        rows.append(prod.ObservedRow(0,0,1,0))
        result = prod.evaluate_prefix(rows,4,m=5)
        self.assertEqual(result['diagnostics']['integrity_reason'],'conflicting_duplicate')
        self.assertEqual(result['decisions']['integrity_adjusted'],'inconclusive')

    def test_unexpected_id_cannot_hide_as_a_future_record(self):
        rows = [prod.ObservedRow(i,0,i%2,i) for i in range(200)]
        rows.append(prod.ObservedRow(999,0,1,0))
        result = prod.evaluate_cohort(rows,m=1)
        self.assertEqual(result['looks'][0]['diagnostics']['invalid_rows'],1)
        self.assertEqual(result['methods']['integrity_adjusted']['decision'],'inconclusive')
        self.assertEqual(result['methods']['integrity_adjusted']['reason'],'integrity_invalid_observed_row')

    def test_mc_paired_interval_matches_paired_sample_statistics(self):
        differences = [-1,0,0,1,1]*400
        result = report.paired_interval(sum(differences),sum(x*x for x in differences),2000)
        mean = statistics.fmean(differences)
        half = 1.959963984540054*statistics.stdev(differences)/math.sqrt(2000)
        self.assertAlmostEqual(result['difference'],mean,places=14)
        self.assertAlmostEqual(result['interval95'][0],mean-half,places=14)
        self.assertAlmostEqual(result['interval95'][1],mean+half,places=14)
        for value in (-1,0,1):
            result = report.paired_interval(2000*value,2000*value*value,2000)
            half = math.sqrt(2*math.log(40)/2000)
            self.assertEqual(result['interval_method'],'conservative_Hoeffding_degenerate_fallback')
            self.assertEqual(result['interval95'],[max(-1,value-half),min(1,value+half)])
            self.assertGreater(result['interval95'][1]-result['interval95'][0],0)

    def test_mc_wilson_extremes_and_symmetry(self):
        n = 2000
        z2 = 1.959963984540054**2
        self.assertEqual(report.wilson(0,n)[0],0)
        self.assertAlmostEqual(report.wilson(0,n)[1],z2/(n+z2),places=14)
        self.assertEqual(report.wilson(n,n)[1],1)
        for k in (1,100,1000,1999):
            low,high = report.wilson(k,n)
            other_low,other_high = report.wilson(n-k,n)
            self.assertAlmostEqual(low,1-other_high,places=14)
            self.assertAlmostEqual(high,1-other_low,places=14)

    def test_reporting_categories_partition_all_cohorts(self):
        for worthwhile,decision in itertools.product((False,True),('ship','hold','inconclusive')):
            vector = report.event_vector(decision,worthwhile)
            self.assertEqual(sum(vector[k] for k in ('false_ship','false_hold','correct_decision','inconclusive')),1)
            self.assertEqual(vector['correct_decision'],vector['correct_ship']+vector['correct_hold'])
            self.assertEqual(vector['false_decision'],vector['false_ship']+vector['false_hold'])


if __name__ == '__main__':
    unittest.main()
