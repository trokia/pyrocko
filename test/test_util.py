from pyrocko import mseed, trace, util, io
import unittest, math, calendar, time
from random import random

class UtilTestCase( unittest.TestCase ):
    
    def testTime(self):
        
        for fmt, accu in zip(
            [ '%Y-%m-%d %H:%M:%S.3FRAC', '%Y-%m-%d %H:%M:%S.2FRAC', '%Y-%m-%d %H:%M:%S.1FRAC', '%Y-%m-%d %H:%M:%S' ],
            [ 0.001, 0.01, 0.1, 1.] ):
        
            ta = util.str_to_time('1960-01-01 10:10:10')
            tb = util.str_to_time('2020-01-01 10:10:10')
            
            for i in xrange(10000):
                t1 = ta + random() * (tb-ta)
                s = util.time_to_str(t1, format=fmt)
                t2 = util.str_to_time(s, format=fmt)
                assert abs( t1 - t2 ) < accu

    def testIterTimes(self):

        tmin = util.str_to_time('1999-03-20 20:10:10')
        tmax = util.str_to_time('2001-05-20 10:00:05')

        ii = 0
        for ymin, ymax in util.iter_years(tmin, tmax):
            for mmin, mmax in util.iter_months(ymin, ymax):
                ii += 1
                s1 = util.time_to_str(mmin)
                s2 = util.time_to_str(mmax)
      
        assert ii == 12*3
        assert s1 == '2001-12-01 00:00:00.000'
        assert s2 == '2002-01-01 00:00:00.000'

if __name__ == "__main__":
    util.setup_logging('test_util', 'warning')
    unittest.main()
    
