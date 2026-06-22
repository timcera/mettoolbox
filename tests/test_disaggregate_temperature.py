"""
test_mettoolbox
----------------------------------

Tests for `mettoolbox` module.
"""

# Standard library imports
import unittest

# Third party imports
from pandas.testing import assert_frame_equal

# First party imports
from mettoolbox import mettoolbox
from mettoolbox.toolbox_utils.src.toolbox_utils import tsutils


class TestMettoolbox(unittest.TestCase):
    def setUp(self):
        self.disaggregate_temperature = tsutils.common_kwds(
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
        assert_frame_equal(
            out,
            self.disaggregate_temperature,
            check_dtype=False,
            check_index_type=False,
        )

    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()
