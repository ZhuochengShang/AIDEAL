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
    output_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/qualified/runs/original/sedonadb/sedonadb/execution/output"
    # TODO API_TEST_START
    table = sd.sql("SELECT ST_AsText(ST_Point(10.0, 20.0, 4326)) as wkt").to_arrow_table()
    wkt_result = table.column("wkt")[0].as_py()

    assert wkt_result == "POINT (10 20)"
    print(f"__CHECK__ sql:ST_Point {wkt_result}")

    table_srid = sd.sql("SELECT ST_SRID(ST_Point(10.0, 20.0, 3857)) as srid").to_arrow_table()
    srid_result = table_srid.column("srid")[0].as_py()

    assert srid_result == 3857
    print(f"__CHECK__ sql:ST_Point {srid_result}")
    # TODO API_TEST_END
    _tracked_connection.verify()
    print("__DONE__")


if __name__ == "__main__":
    main()

