from ..deprivation_scores.constants.scottish_postcodes import (
    SCOTTISH_IMD_TEST_DATA,
    SCOTTISH_POSTCODES,
    SCOTTISH_ADDRESSES,
)


class ScottishTests:
    def test_imd_rank_for_data_zone_code(self):
        imd_rank = SCOTTISH_IMD_TEST_DATA
