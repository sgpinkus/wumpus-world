import unittest
from unittest import TestCase
from directions import *


class TestDirections(TestCase):

  def test_test(self):
     print(known_path('EEEEEESEEENW', 'EEEEEESEEE', Hood4))

if __name__ == '__main__':
    unittest.main()
