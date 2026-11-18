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
            // AIDEAL_DATA_BINDINGS
            // TODO API_TEST_START
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
