from pathlib import Path
import math
import json
from sedona_runtime import TrackedContext, requested_sql_target


def main():
    _, target_api = requested_sql_target(__file__)
    sd = TrackedContext(target_api)
    _tracked_connection = sd
    # AIDEAL_DATA_BINDINGS
    # TODO API_TEST_START
    raise AssertionError("Audience snippet was not inserted")
    # TODO API_TEST_END
    _tracked_connection.verify()
    print("__DONE__")


if __name__ == "__main__":
    main()

