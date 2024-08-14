import unittest

import lz4.frame


class MainFunctionsTestCase(unittest.TestCase):
    def test_compressing(self):
        dom = "this is a test dom"
        compressed = lz4.frame.compress(bytes(dom, 'utf-8'))
        decompressed = lz4.frame.decompress(compressed)
        self.assertEqual(dom, decompressed.decode())  # add assertion here


if __name__ == '__main__':
    unittest.main()
