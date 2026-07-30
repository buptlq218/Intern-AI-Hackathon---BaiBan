"""跑一遍策略引擎的全部回归用例。

现场每次改完 TUNE 参数都跑这个。它不碰网络、不需要 SDK，一秒内出结果。

    python mytests/run_all.py
"""

import os
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)


def main():
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.dirname(os.path.abspath(__file__)),
                            pattern="test_*.py", top_level_dir=BASE)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
