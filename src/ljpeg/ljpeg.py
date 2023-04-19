import argparse
import glob
import logging
import os
import re
import subprocess
import sys

import cv2
import numpy

from ljpeg import __version__
from ljpeg.utils import get_ics_info

__author__ = "sanchezcarlosjr"
__copyright__ = "sanchezcarlosjr"
__license__ = "MIT"

_logger = logging.getLogger(__name__)

BIN = os.path.join(os.path.dirname(__file__), "jpegdir", "jpeg_static")

if not os.path.exists(BIN):
    _logger.error("jpeg is not built yet; use 'cd jpegdir; make' first")
    sys.exit(0)

# sample output
# > GW:1979  GH:4349  R:0
# >> C:1  N:xx.ljpeg.1  W:1979  H:4349  hf:1  vf:1

PATTERN = re.compile(r"\sC:(\d+)\s+N:(\S+)\s+W:(\d+)\s+H:(\d+)\s")


def od_correct(im, ics_info):
    """
    Map gray levels to optical density level
    :param im: image (numpy)
    :return: optical density image
    """
    im_od = numpy.zeros_like(im, dtype=numpy.float64)

    if (ics_info['scan_institution'] == 'MGH') and (ics_info['scanner_type'] == 'DBA'):
        im_od = (numpy.log10(im + 1) - 4.80662) / -1.07553
    elif (ics_info['scan_institution'] == 'MGH') \
            and (ics_info['scanner_type'] == 'HOWTEK'):
        im_od = (-0.00094568 * im) + 3.789
    elif (ics_info['scan_institution'] == 'WFU') \
            and (ics_info['scanner_type'] == 'LUMISYS'):
        im_od = (im - 4096.99) / -1009.01
    elif (ics_info['scan_institution'] == 'ISMD') \
            and (ics_info['scanner_type'] == 'HOWTEK'):
        im_od = (-0.00099055807612 * im) + 3.96604095240593

    # perform heath noise correction
    im_od[im_od < 0.05] = 0.05
    im_od[im_od > 3.0] = 3.0
    return im_od


def read(path):
    cmd = "{} -d -s {}".format(BIN, path)
    output = subprocess.check_output(cmd, shell=True)
    _logger.debug(output)
    m = re.search(PATTERN, output.decode())
    C = int(m.group(1))  # I suppose this is # channels
    F = m.group(2)
    W = int(m.group(3))
    H = int(m.group(4))
    assert C == 1
    im = numpy.fromfile(F, dtype="uint16").reshape(H, W)
    L = im >> 8
    H = im & 0xFF
    im = (H << 8) | L
    os.remove(F)
    return im


def run():
    parser = argparse.ArgumentParser(description="Read and transform LJPEG images")
    parser.add_argument(
        "--version",
        action="version",
        version=f"ljpeg {__version__}",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
        )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    parser.add_argument("ljpeg", nargs=1)
    parser.add_argument("output", nargs=1)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--visual", action="store_true")
    parser.add_argument("--ics_info",
                        action="store_true",
                        help="display ics info as dict")
    parser.add_argument("--od_correct",
                        action="store_true",
                        help="map gray levels to optical density level")
    parser.add_argument("--scale", type=float)

    args = parser.parse_args()
    path = args.ljpeg[0]
    tiff = args.output[0]

    assert "LJPEG" in path

    root = os.path.dirname(path)
    _logger.debug(root)
    stem = os.path.splitext(path)[0]
    _logger.debug(stem)

    # read ICS
    _logger.info(glob.glob(root + "/*.ics"))
    ics = glob.glob(root + "/*.ics")[0]
    name = path.split(".")[-2]

    W = None
    H = None
    ics_info = get_ics_info(ics)
    W = ics_info[name]['width']
    H = ics_info[name]['height']
    if ics_info[name]['bpp'] != 12:
        _logger.warning("BPS != 12: %s" % path)

    if args.ics_info:
        print(ics_info)

    assert W is not None
    assert H is not None

    image = read(path)

    if W != image.shape[1]:
        _logger.warning("reshape: %s" % path)
        image = image.reshape((H, W))

    raw = image

    if args.od_correct:
        image = od_correct(image, ics_info)
        image = numpy.interp(image, (0.0, 4.0), (255, 0))
        image = image.astype(numpy.uint8)

    if args.visual:
        _logger.warning("normalizing color, will lose information")
        if args.verify:
            _logger.error("verification is going to fail")
        if args.scale:
            rows, cols = image.shape
            image = cv2.resize(image, (int(cols * args.scale), int(rows * args.scale)))
        image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
        image = numpy.uint8(image)
    elif args.scale:
        _logger.error("--scale must be used with --visual")
        sys.exit(1)
    cv2.imwrite(tiff, image)

    if args.verify:
        verify = cv2.imread(tiff, -1)
        if numpy.all(raw == verify):
            print("Verification successful, conversion is lossless")
        else:
            _logger.error("Verification failed: %s" % path)


if __name__ == "__main__":
    run()
