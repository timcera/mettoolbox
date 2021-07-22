# -*- coding: utf-8 -*-

"""
test_mettoolbox
----------------------------------

Tests for `mettoolbox` module.
"""

import unittest

from pandas.testing import assert_frame_equal
from tstoolbox import tstoolbox

from mettoolbox import mettoolbox


class TestMettoolbox(unittest.TestCase):
    def setUp(self):
        self.disaggregate_temperature = tstoolbox.read(
            "tests/data_temperature_gainesville_disaggregate_sine_mean.csv"
        )

    def test_disaggregate_temperature(self):
        out = mettoolbox.disaggregate.temperature(
            "sine_mean",
            ["degC", "degC"],
            temp_min_col=1,
            temp_max_col=2,
            input_ts="tests/data_temperature_gainesville.csv",
        )
        out.index.name = "Datetime"
        assert_frame_equal(out, self.disaggregate_temperature, check_dtype=False)

    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()
