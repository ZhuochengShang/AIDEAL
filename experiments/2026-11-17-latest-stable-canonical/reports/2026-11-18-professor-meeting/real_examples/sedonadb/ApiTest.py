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
    output_dir = r"/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/explicit-inputs-r0/continuation/sedonadb/generated_d1/execution/run_sql_ST_Distance--8bed70b7baaedb77e88e151d5fb938563729570191d96e27fb565ca1ab1eebd5/attempt_0001/output"
    # TODO API_TEST_START
    table_geom = sd.sql("SELECT ST_Distance(ST_Point(0.0, 0.0), ST_Point(3.0, 4.0)) as dist").to_arrow_table()
    dist_geom = table_geom.column("dist")[0].as_py()
    assert abs(dist_geom - 5.0) < 1e-9
    print(f"__CHECK__ sql:ST_Distance {dist_geom}")

    table_geog = sd.sql("SELECT ST_Distance(ST_GeogPoint(0.0, 0.0), ST_GeogPoint(0.0, 1.0)) as dist").to_arrow_table()
    dist_geog = table_geog.column("dist")[0].as_py()
    # 1 degree of latitude is approximately 111,319 meters
    assert dist_geog > 110000 and dist_geog < 112000
    print(f"__CHECK__ sql:ST_Distance {dist_geog}")
    # TODO API_TEST_END
    _tracked_connection.verify()
    print("__DONE__")


if __name__ == "__main__":
    main()

