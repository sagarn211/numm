import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from extract_attributes import extract_attributes  # noqa: E402
from normalize import normalize  # noqa: E402


class IndustrialAttributeTests(unittest.TestCase):
    def extract(self, value):
        return extract_attributes(normalize(value))

    def test_flanged_ball_valve_remains_a_valve(self):
        attrs = self.extract("BALL VALVE SS316 DN50 PN16 FLANGED")
        self.assertEqual(attrs["family"], "VALVE")
        self.assertEqual(attrs["valve_type"], "BALL")
        self.assertEqual(attrs["nominal_diameter"], "DN50")
        self.assertEqual(attrs["pressure_rating"], "PN16")

    def test_motor_attributes_are_normalized(self):
        attrs = self.extract("INDUCTION MOTOR 45 KW 415 V 3 PH 50 HZ 1480 RPM FRAME 225M IP55 IE3")
        self.assertEqual(attrs["family"], "MOTOR")
        self.assertEqual(attrs["voltage"], "415V")
        self.assertEqual(attrs["phase"], "3PH")
        self.assertEqual(attrs["efficiency_class"], "IE3")

    def test_bearing_designation_and_dimensions(self):
        attrs = self.extract("SKF DEEP GROOVE BALL BEARING 6205 25 X 52 X 15 MM 2RS")
        self.assertEqual(attrs["bearing_designation"], "6205")
        self.assertEqual((attrs["bore"], attrs["outer_diameter"], attrs["width"]), ("25MM", "52MM", "15MM"))

    def test_pipe_attributes(self):
        attrs = self.extract('CARBON STEEL PIPE 4 INCH SCH40 ASME B36.10 BUTT WELD')
        self.assertEqual(attrs["family"], "PIPE")
        self.assertEqual(attrs["nominal_diameter"], "101.6MM")
        self.assertEqual(attrs["schedule"], "SCH40")


if __name__ == "__main__":
    unittest.main()
