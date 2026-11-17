from pathlib import Path
import math
import json
from sedona_runtime import TrackedContext


def main():
    target_api = Path(__file__).parent.name.removeprefix("run_")
    sd = TrackedContext(target_api)
    _tracked_connection = sd
    # AIDEAL_DATA_BINDINGS
    # TODO API_TEST_START
    table = sd.sql("SELECT ST_Area(ST_GeomFromWKT('POLYGON ((0 0, 2 0, 2 3, 0 3, 0 0))')) AS value").to_arrow_table()
    value = table.column("value")[0].as_py()
    assert value == 7.0
    print("__CHECK__ ST_Area area=7.0")
    # TODO API_TEST_END
    _tracked_connection.verify()
    print("__DONE__")


if __name__ == "__main__":
    main()

