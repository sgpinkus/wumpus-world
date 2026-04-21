import unittest
from unittest import TestCase
from utils import Location, Move, path_of, path_to, map4

test_tree: dict[Location, Move] = {
    (0, 1): Move((0, 0), 'S'),
    (0, 2): Move((0, 1), 'S'),
    (1, 2): Move((0, 2), 'E'),
    (0, 3): Move((0, 2), 'S'),
    (0, 4): Move((0, 3), 'S')
}


class TestUtils(TestCase):

  def test_path_of(self):
    self.assertEqual(path_of((0, 3), test_tree), ['S', 'S', 'S'])
    self.assertEqual((path_of((1, 2), test_tree)), ['S', 'S', 'E'])
    self.assertEqual(path_of((10, 10), test_tree), [])

  def test_path_to(self):
    self.assertEqual(path_to((0, 4), (1, 2), test_tree, map4), ['N', 'N', 'E'])


if __name__ == '__main__':
  unittest.main()
