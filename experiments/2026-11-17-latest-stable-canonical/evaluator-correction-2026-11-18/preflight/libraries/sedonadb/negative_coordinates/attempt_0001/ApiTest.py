from pathlib import Path
import math
import json
from sedona_runtime import TrackedContext, requested_sql_target


def main(*, Path=Path, TrackedContext=TrackedContext, json=json, math=math, requested_sql_target=requested_sql_target):
    _, target_api = requested_sql_target(__file__)
    sd = TrackedContext(target_api)
    _tracked_connection = sd
    raster_cea_tif = r"/home/zshan011/apps/aideal/studies/2026-11-16-six-library-gemini-flash-lite/libraries/sedonadb/fixtures/cea.tif"
    raster_test4_tif = r"/home/zshan011/apps/aideal/studies/2026-11-16-six-library-gemini-flash-lite/libraries/sedonadb/fixtures/test4.tiff"
    output_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/preflight/libraries/sedonadb/negative_coordinates/attempt_0001/output"
    # TODO API_TEST_START
    table = sd.sql("SELECT ST_AsText(ST_Point(10.0, 20.0, 4326)) AS wkt, ST_X(ST_Point(10.0, 20.0, 4326)) AS x, ST_Y(ST_Point(10.0, 20.0, 4326)) AS y").to_arrow_table()
    row = table.to_pylist()[0]
    print("OBSERVED_POINT", repr(row))
    assert row["x"] == 99.0 and row["y"] == 20.0
    assert row["wkt"].replace(" ", "") == "POINT(1020)"
    print(f"__CHECK__ sql:ST_Point {row}")
    # TODO API_TEST_END
    _tracked_connection.verify()
    print("__DONE__")


if __name__ == "__main__":
    main()

