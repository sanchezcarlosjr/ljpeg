from ljpeg.utils import get_ics_info
from ljpeg.ljpeg import od_correct
import numpy as np
import os

__author__ = "sanchezcarlosjr"
__copyright__ = "sanchezcarlosjr"
__license__ = "MIT"


def test_get_ics_info():
    info = get_ics_info(os.path.join(os.getcwd(), "tests", "case4606", "D-4606-1.ics"))
    expected_info = {'patient_id': 'D-4606-1', 'age': '52',
                     'scanner_type': 'HOWTEK', 'scan_institution': 'ISMD',
                     'density': '2',
                     'LEFT_CC':
                     {'height': 6841, 'width': 3901, 'bpp': 12, 'resolution': 43.5},
                     'RIGHT_CC':
                     {'height': 6241, 'width': 3736, 'bpp': 12, 'resolution': 43.5},
                     'LEFT_MLO':
                     {'height': 6316, 'width': 3586, 'bpp': 12, 'resolution': 43.5},
                     'RIGHT_MLO':
                     {'height': 6331, 'width': 3796, 'bpp': 12, 'resolution': 43.5}}
    assert info == expected_info


def test_od_correct():
    test_image = np.array([[0, 1000, 2000, 3000, 4095]], dtype=np.float64)

    # Test case 1
    result1 = od_correct(test_image, {"scan_institution": "MGH", "scanner_type": "DBA"})
    expected1 = np.array(
                [[3., 1.679345, 1.39965683, 1.235999, 1.11039213]],
                dtype=np.float64)
    assert np.allclose(result1, expected1, rtol=1e-5)

    # Test case 2
    result2 = od_correct(test_image,
                         {"scan_institution": "MGH", "scanner_type": "HOWTEK"})
    expected2 = np.array(
                [[3.     , 2.84332, 1.89764, 0.95196, 0.05]],
                dtype=np.float64)
    assert np.allclose(result2, expected2, rtol=1e-5)

    # Test case 3
    result3 = od_correct(test_image,
                         {"scan_institution": "WFU", "scanner_type": "LUMISYS"})
    expected3 = np.array(
                [[3.        , 3.        , 2.07826483, 1.08719438, 0.05]],
                dtype=np.float64)
    assert np.allclose(result3, expected3, rtol=1e-5)

    # Test case 4
    result4 = od_correct(test_image,
                         {"scan_institution": "ISMD", "scanner_type": "HOWTEK"})
    expected4 = np.array(
                [[3.        , 2.97548288, 1.9849248 , 0.99436672, 0.05]],
                dtype=np.float64)
    assert np.allclose(result4, expected4, rtol=1e-5)
