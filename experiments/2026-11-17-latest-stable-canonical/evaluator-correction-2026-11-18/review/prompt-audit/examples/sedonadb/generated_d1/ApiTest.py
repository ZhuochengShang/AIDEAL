from pathlib import Path
import math
import json
from sedona_runtime import TrackedContext, requested_sql_target


def main():
    _, target_api = requested_sql_target(__file__)
    sd = TrackedContext(target_api)
    _tracked_connection = sd
    raster_cea_tif = r"/home/zshan011/apps/aideal/studies/2026-11-16-six-library-gemini-flash-lite/libraries/sedonadb/fixtures/cea.tif"
    raster_test4_tif = r"/home/zshan011/apps/aideal/studies/2026-11-16-six-library-gemini-flash-lite/libraries/sedonadb/fixtures/test4.tiff"
    output_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/sedonadb/execution/output"
    # TODO API_TEST_START
    x, y = -74.0060, 40.7128
    srid = 4326
    query = f"SELECT ST_AsText(ST_Point({x}, {y}, {srid})) as wkt"
    result = sd.sql(query).to_arrow_table()
    wkt = result.column("wkt")[0].as_py()

    # Verify the WKT format matches the input coordinates
    assert wkt == "POINT (-74.006 40.7128)", f"Expected POINT (-74.006 40.7128), got {wkt}"

    print(f"__CHECK__ sql:ST_Point {wkt}")
    # TODO API_TEST_END
    _tracked_connection.verify()
    print("__DONE__")


if __name__ == "__main__":
    main()

