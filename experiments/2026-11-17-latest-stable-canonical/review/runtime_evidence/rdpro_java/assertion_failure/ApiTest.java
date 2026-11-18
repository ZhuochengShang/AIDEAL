import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.awt.geom.AffineTransform;
import org.apache.spark.SparkConf;
import org.apache.spark.api.java.JavaSparkContext;
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.sql.SparkSession;
import org.locationtech.jts.geom.*;
import edu.ucr.cs.bdlab.beast.common.BeastOptions;
import edu.ucr.cs.bdlab.beast.geolite.*;
import edu.ucr.cs.bdlab.beast.cg.*;
import edu.ucr.cs.bdlab.beast.indexing.*;
import edu.ucr.cs.bdlab.beast.io.*;
import edu.ucr.cs.bdlab.beast.util.*;
import edu.ucr.cs.bdlab.raptor.*;
import edu.ucr.cs.bdlab.davinci.*;

public final class ApiTest {
    public static void main(String[] args) {
        JavaSparkContext sc = null;
        try {
            sc = new JavaSparkContext(new SparkConf().setAppName("RDProJavaNative").setMaster("local[2]").set("spark.ui.enabled", "false"));
            sc.setLogLevel("ERROR");
            SparkSession spark = SparkSession.builder().sparkContext(sc.sc()).getOrCreate();
            String vector_shapefile = "/home/zshan011/apps/aideal/studies/2026-11-17-full-rdpro/inputs/fixtures/Boston_Neighborhood_Boundaries_sample_grail.shp";
    String raster_tif = "/home/zshan011/apps/aideal/studies/2026-11-17-full-rdpro/inputs/fixtures/nldas_boston_30m.tif";
    String hdf_file = "/home/zshan011/apps/aideal/studies/2026-11-17-full-rdpro/inputs/fixtures/sample.hdf";
    String output_dir = "/home/zshan011/apps/aideal/checks/2026-11-17-latest-stable-runtime/native-java-a6-control-v2/assertion_failure/execution/output";

    // pre-loaded typed inputs (comprehension.execute.preamble)
    EnvelopeNDLite envelope = new EnvelopeNDLite(2, 0.0, 0.0, 2.0, 3.0);
    GeometryFactory geometryFactory = new GeometryFactory();
    Point point = geometryFactory.createPoint(new Coordinate(1.0, 2.0));
    RasterMetadata metadata = new RasterMetadata(0, 0, 4, 4, 2, 2, 4326, new AffineTransform());
    JavaRDD<Integer> numbers = sc.parallelize(Arrays.asList(1, 2, 3), 1);
    Files.createDirectories(Paths.get(output_dir));
            // TODO API_TEST_START
            edu.ucr.cs.bdlab.beast.geolite.EmptyGeometry value = edu.ucr.cs.bdlab.beast.geolite.EmptyGeometry.instance;
            if (value.getArea() != 0.0) throw new AssertionError("empty area");
            Class<?> owner = value.getClass();
            String origin = java.nio.file.Paths.get(owner.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath().toString();
            if (!origin.equals("/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/runtime/rdpro-stable-source-build/artifacts/beast-stable-production-0.10.1.jar")) throw new AssertionError("fresh stable source origin");
            System.out.println("__IDENTITY__ " + owner.getName() + " " + origin);
            System.out.println("__CHECK__ getArea deterministic native control");
            if (value != null) throw new AssertionError("AIDEAL_EXPECTED_ASSERTION_FAILURE");
            // TODO API_TEST_END
            System.out.println("__DONE__");
        } catch (Throwable exc) {
            System.err.println("__RUN_ERR__ " + exc.getClass().getSimpleName() + ": " + exc.getMessage());
            exc.printStackTrace(System.err);
            System.exit(1);
        } finally {
            if (sc != null) sc.close();
        }
    }
}
