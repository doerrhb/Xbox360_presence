import sys

import requests

from presence_service import ConfigError, run_foreground


def main() -> None:
    ip_override = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        run_foreground(ip_override=ip_override)
    except ConfigError as exc:
        print(exc, flush=True)
        sys.exit(1)
    except requests.RequestException:
        sys.exit(1)


if __name__ == "__main__":
    main()
