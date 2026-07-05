from __future__ import annotations

import sys

from rocket2d.bootstrap import ensure_dependencies


def main() -> None:
    ensure_dependencies()

    from rocket2d.game import Rocket2D, run_self_test

    if "--self-test" in sys.argv:
        run_self_test()
        return

    Rocket2D().run()


if __name__ == "__main__":
    main()
