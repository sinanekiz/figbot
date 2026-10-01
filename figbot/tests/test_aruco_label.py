import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import cv2
import numpy as np
from pypdf import PdfReader
from scripts.build_aruco_label import build, marker_pixels
from scripts import publish_current


class ArucoLabelTests(unittest.TestCase):
    def test_marker_all_rotations(self):
        detector=cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50))
        for turns in range(4):
            corners,ids,_=detector.detectMarkers(np.ascontiguousarray(np.rot90(marker_pixels(),turns)))
            self.assertEqual(ids.flatten().tolist(),[0])
            self.assertEqual(len(corners),1)

    def test_a4_and_size_instructions(self):
        with tempfile.TemporaryDirectory() as directory:
            build(directory)
            reader=PdfReader(Path(directory)/'ARUCO_KISKAC_A4.pdf')
            self.assertEqual(len(reader.pages),1)
            self.assertAlmostEqual(float(reader.pages[0].mediabox.width)*25.4/72,210,places=3)
            self.assertIn('36 × 36 mm',reader.pages[0].extract_text())

    def test_isolated_publication_dispatch(self):
        with patch('sys.argv',['publish_current','--aruco-label']),patch('scripts.build_aruco_label.publish') as action:
            publish_current.main();action.assert_called_once_with()
        with patch('sys.argv',['publish_current','--aruco-label','--servo-test']),contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):publish_current.main()
