import unittest
from funkload.ReportStats import StatsAccumulator, StatsAggregator

class TestStatsAccumulator(unittest.TestCase):
    def setUp(self):
        self.accum = StatsAccumulator(10, 1.5)
        for t, i in [(7.1, 4), (7.2, 2), (1.2, 3), (2.1, 1), (3.1, 0)]:
            self.accum.add_record(t, i, i % 2 == 0)

    def test_min(self):
        self.assertEquals(0, self.accum.min)

    def test_max(self):
        self.assertEquals(4, self.accum.max)

    def test_successes(self):
        self.assertEquals(3, self.accum.successes)

    def test_errors(self):
        self.assertEquals(2, self.accum.errors)

    def test_ordered_values(self):
        self.assertEquals([0,1,2,3,4], list(self.accum.ordered_values))

    def test_total(self):
        self.assertEquals(10, self.accum.total)

    def test_percentiles(self):
        self.accum.compute_percentiles(10)
        self.assertEquals(0, self.accum.perc10)
        self.assertEquals(1, self.accum.perc20)
        self.assertEquals(1, self.accum.perc30)
        self.assertEquals(2, self.accum.perc40)
        self.assertEquals(2, self.accum.perc50)
        self.assertEquals(3, self.accum.perc60)
        self.assertEquals(3, self.accum.perc70)
        self.assertEquals(4, self.accum.perc80)
        self.assertEquals(4, self.accum.perc90)

        self.accum.compute_percentiles(1)
        self.assertEquals(0, self.accum.perc1)
        self.assertEquals(0, self.accum.perc13)
        self.assertEquals(4, self.accum.perc99)

        self.assertRaises(ValueError, self.accum.compute_percentiles, 3.3)

    def test_apdex_raw_score(self):
        self.assertEquals(3.5, self.accum.apdex.raw_score)

    def test_apdex_score(self):
        self.assertEquals(3.5/5, self.accum.apdex_score)

    def test_avg_per_second(self):
        self.assertEquals(.5, self.accum.avg_per_second)

    def test_min_per_second(self):
        self.assertEquals(0, self.accum.min_per_second)

    def test_max_per_second(self):
        self.assertEquals(2, self.accum.max_per_second)

class TestStatsAggregator(unittest.TestCase):
    def setUp(self):
        self.accums = [StatsAccumulator(10, 1.5), StatsAccumulator(10, 1.5)]
        self.aggr = StatsAggregator(self.accums)
        
        for t, i in [(0, 10), (1, 1), (2, 7), (3, 10)]:
            self.accums[0].add_record(t, i, i % 2 == 0)

        for t, i in [(0, 5), (0, 13), (0, 6)]:
            self.accums[1].add_record(t, i, i % 2 == 0)

    def test_min(self):
        self.assertEquals(1, self.aggr.min)

    def test_max(self):
        self.assertEquals(13, self.aggr.max)

    def test_successes(self):
        self.assertEquals(3, self.aggr.successes)

    def test_errors(self):
        self.assertEquals(4, self.aggr.errors)

    def test_ordered_values(self):
        self.assertEquals([1,5,6,7,10,10,13], list(self.aggr.ordered_values))

    def test_total(self):
        self.assertEquals(52, self.aggr.total)

    def test_percentiles(self):
        self.aggr.compute_percentiles(10)
        self.assertEquals(1, self.aggr.perc10)
        self.assertEquals(5, self.aggr.perc20)
        self.assertEquals(6, self.aggr.perc30)
        self.assertEquals(6, self.aggr.perc40)
        self.assertEquals(7, self.aggr.perc50)
        self.assertEquals(10, self.aggr.perc60)
        self.assertEquals(10, self.aggr.perc70)
        self.assertEquals(10, self.aggr.perc80)
        self.assertEquals(13, self.aggr.perc90)

        self.aggr.compute_percentiles(1)
        self.assertEquals(1, self.aggr.perc1)
        self.assertEquals(1, self.aggr.perc13)
        self.assertEquals(13, self.aggr.perc99)

        self.assertRaises(ValueError, self.aggr.compute_percentiles, 3.3)

    def test_apdex_score(self):
        self.assertEquals(1.5/7, self.aggr.apdex_score)

    def test_avg_per_second(self):
        self.assertEquals(7.0/10, self.aggr.avg_per_second)

    def test_min_per_second(self):
        self.assertEquals(0, self.aggr.min_per_second)

    def test_max_per_second(self):
        self.assertEquals(4, self.aggr.max_per_second)
