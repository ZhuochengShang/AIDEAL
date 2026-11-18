// AIDEAL API-test scaffold — AUTO-GENERATED from the API surface.
// Run via: spark-shell --jars <uberjar> -i <thisfile>
// spark-shell provides `sc` (SparkContext) and `spark` (SparkSession).
// The generated snippet is spliced between API_TEST_START / END and may use
// the in-scope bindings: sc, inputA, inputB, output.

import org.apache.spark.SparkContext
import org.apache.spark.sql.{SparkSession, DataFrame, Row}
import org.apache.spark.rdd.RDD
import edu.ucr.cs.bdlab.raptor._
import edu.ucr.cs.bdlab.beast.JavaSpatialRDDHelper
import edu.ucr.cs.bdlab.beast.JavaSpatialSparkContext
import edu.ucr.cs.bdlab.beast.SpatialOperationsMixin
import edu.ucr.cs.bdlab.beast.cg.CGOperationsMixin
import edu.ucr.cs.bdlab.beast.cg.GeometryQuadSplitter
import edu.ucr.cs.bdlab.beast.cg.PlaneSweepSelfJoinIterator
import edu.ucr.cs.bdlab.beast.cg.PlaneSweepSpatialJoinIterator
import edu.ucr.cs.bdlab.beast.cg.Reprojector
import edu.ucr.cs.bdlab.beast.cg.SnapTransform
import edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes
import edu.ucr.cs.bdlab.beast.cg.SpatialJoinHelper
import edu.ucr.cs.bdlab.beast.cg.SpatialPartition
import edu.ucr.cs.bdlab.beast.common.BeastOptions
import edu.ucr.cs.bdlab.beast.common.BlockCartesianRDD
import edu.ucr.cs.bdlab.beast.common.CLIOperation
import edu.ucr.cs.bdlab.beast.common.JCLIOperation
import edu.ucr.cs.bdlab.beast.dataExplorer.DataExplorerServer
import edu.ucr.cs.bdlab.beast.dataExplorer.DatasetProcessor
import edu.ucr.cs.bdlab.beast.dataExplorer.SQLQueryHelper
import edu.ucr.cs.bdlab.beast.dataExplorer.WorkspaceProcessor
import edu.ucr.cs.bdlab.beast.generator.BitGenerator
import edu.ucr.cs.bdlab.beast.generator.DiagonalGenerator
import edu.ucr.cs.bdlab.beast.generator.DistributionType
import edu.ucr.cs.bdlab.beast.generator.GaussianGenerator
import edu.ucr.cs.bdlab.beast.generator.JavaSpatialGeneratorBuilder
import edu.ucr.cs.bdlab.beast.generator.ParcelGenerator
import edu.ucr.cs.bdlab.beast.generator.PointBasedGenerator
import edu.ucr.cs.bdlab.beast.generator.RandomSpatialRDD
import edu.ucr.cs.bdlab.beast.generator.SierpinskiGenerator
import edu.ucr.cs.bdlab.beast.generator.SpatialGenerator
import edu.ucr.cs.bdlab.beast.generator.SpatialGeneratorBuilder
import edu.ucr.cs.bdlab.beast.generator.UniformGenerator
import edu.ucr.cs.bdlab.beast.geolite.DefaultReadOnlyTile
import edu.ucr.cs.bdlab.beast.geolite.Feature
import edu.ucr.cs.bdlab.beast.geolite.IFeature
import edu.ucr.cs.bdlab.beast.geolite.ITile
import edu.ucr.cs.bdlab.beast.geolite.ITileSerializer
import edu.ucr.cs.bdlab.beast.geolite.RasterFeature
import edu.ucr.cs.bdlab.beast.geolite.RasterFeatureSerializer
import edu.ucr.cs.bdlab.beast.geolite.RasterMetadata
import edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer
import edu.ucr.cs.bdlab.beast.geolite.RasterSchemaHelper
import edu.ucr.cs.bdlab.beast.indexing.IndexHelper
import edu.ucr.cs.bdlab.beast.indexing.IndexMixin
import edu.ucr.cs.bdlab.beast.io.CSVHelper
import edu.ucr.cs.bdlab.beast.io.CSVReaderLite
import edu.ucr.cs.bdlab.beast.io.Cat
import edu.ucr.cs.bdlab.beast.io.GPXReader
import edu.ucr.cs.bdlab.beast.io.JSONWKTSource
import edu.ucr.cs.bdlab.beast.io.JsonWKTWriter
import edu.ucr.cs.bdlab.beast.io.RTreeSource
import edu.ucr.cs.bdlab.beast.io.ReadWriteMixin
import edu.ucr.cs.bdlab.beast.io.SpatialCSVSource
import edu.ucr.cs.bdlab.beast.io.SpatialFilePartition2
import edu.ucr.cs.bdlab.beast.io.SpatialFilePartitioner
import edu.ucr.cs.bdlab.beast.io.SpatialFileRDD
import edu.ucr.cs.bdlab.beast.io.SpatialFileSource
import edu.ucr.cs.bdlab.beast.io.SpatialParquetSource
import edu.ucr.cs.bdlab.beast.io.SpatialReader
import edu.ucr.cs.bdlab.beast.io.SpatialWriteMessage
import edu.ucr.cs.bdlab.beast.io.SpatialWriter
import edu.ucr.cs.bdlab.beast.io.SupportsSpatialFilterPushDown
import edu.ucr.cs.bdlab.beast.io.geojsonv2.GeoJSONFormat
import edu.ucr.cs.bdlab.beast.io.geojsonv2.GeoJSONPartitionReaderFactory
import edu.ucr.cs.bdlab.beast.io.geojsonv2.GeoJSONReader
import edu.ucr.cs.bdlab.beast.io.geojsonv2.GeoJSONScan
import edu.ucr.cs.bdlab.beast.io.geojsonv2.GeoJSONScanBuilder
import edu.ucr.cs.bdlab.beast.io.geojsonv2.GeoJSONSourcev2
import edu.ucr.cs.bdlab.beast.io.geojsonv2.GeoJSONTable
import edu.ucr.cs.bdlab.beast.io.geojsonv2.GeoJSONWriter
import edu.ucr.cs.bdlab.beast.io.gpxv2.GPXPartitionReaderFactory
import edu.ucr.cs.bdlab.beast.io.gpxv2.GPXReader2
import edu.ucr.cs.bdlab.beast.io.gpxv2.GPXScan
import edu.ucr.cs.bdlab.beast.io.gpxv2.GPXScanBuilder
import edu.ucr.cs.bdlab.beast.io.gpxv2.GPXSource
import edu.ucr.cs.bdlab.beast.io.gpxv2.GPXTable
import edu.ucr.cs.bdlab.beast.io.kmlv2.KMLFormat
import edu.ucr.cs.bdlab.beast.io.kmlv2.KMLSourcev2
import edu.ucr.cs.bdlab.beast.io.kmlv2.KMLWriter
import edu.ucr.cs.bdlab.beast.io.kmlv2.KMZFormat
import edu.ucr.cs.bdlab.beast.io.kmlv2.KMZSourcev2
import edu.ucr.cs.bdlab.beast.io.shapefilev2.AbstractShapefileReader
import edu.ucr.cs.bdlab.beast.io.shapefilev2.CompressedShapefileReader
import edu.ucr.cs.bdlab.beast.io.shapefilev2.DBFHeader
import edu.ucr.cs.bdlab.beast.io.shapefilev2.DBFHelper
import edu.ucr.cs.bdlab.beast.io.shapefilev2.DBFReader
import edu.ucr.cs.bdlab.beast.io.shapefilev2.DBFWriter
import edu.ucr.cs.bdlab.beast.io.shapefilev2.ShapefileDataSourcev2
import edu.ucr.cs.bdlab.beast.io.shapefilev2.ShapefileFormat
import edu.ucr.cs.bdlab.beast.io.shapefilev2.ShapefileGeometryReader
import edu.ucr.cs.bdlab.beast.io.shapefilev2.ShapefileGeometryWriter
import edu.ucr.cs.bdlab.beast.io.shapefilev2.ShapefileHeader
import edu.ucr.cs.bdlab.beast.io.shapefilev2.ShapefileHelper
import edu.ucr.cs.bdlab.beast.io.shapefilev2.ShapefilePartitionReaderFactory
import edu.ucr.cs.bdlab.beast.io.shapefilev2.ShapefileReader
import edu.ucr.cs.bdlab.beast.io.shapefilev2.ShapefileScan
import edu.ucr.cs.bdlab.beast.io.shapefilev2.ShapefileScanBuilder
import edu.ucr.cs.bdlab.beast.io.shapefilev2.ShapefileTable
import edu.ucr.cs.bdlab.beast.io.shapefilev2.ShapefileWriter
import edu.ucr.cs.bdlab.beast.operations.FeatureWriterSize
import edu.ucr.cs.bdlab.beast.operations.GeometricSummary
import edu.ucr.cs.bdlab.beast.operations.GriddedSummary
import edu.ucr.cs.bdlab.beast.operations.Histogram
import edu.ucr.cs.bdlab.beast.operations.Index
import edu.ucr.cs.bdlab.beast.operations.RasterThumbnail
import edu.ucr.cs.bdlab.beast.operations.SpatialIntersectionRDD
import edu.ucr.cs.bdlab.beast.operations.SpatialJoin
import edu.ucr.cs.bdlab.beast.satex.ImageExtractor
import edu.ucr.cs.bdlab.beast.satex.ImageIterator
import edu.ucr.cs.bdlab.beast.sql.CreationFunctions
import edu.ucr.cs.bdlab.beast.sql.RasterMetadataType
import edu.ucr.cs.bdlab.beast.sql.ST_BreakLine
import edu.ucr.cs.bdlab.beast.sql.ST_Connect
import edu.ucr.cs.bdlab.beast.sql.ST_CreateLinePolygon
import edu.ucr.cs.bdlab.beast.sql.ST_FromSpatialParquet
import edu.ucr.cs.bdlab.beast.sql.ST_ToSpatialParquet
import edu.ucr.cs.bdlab.beast.sql.SpatialParquetHelper
import edu.ucr.cs.bdlab.beast.sql.SpatialPredicates
import edu.ucr.cs.bdlab.beast.synopses.BoxCounting
import edu.ucr.cs.bdlab.beast.synopses.GeometryToPoints
import edu.ucr.cs.bdlab.beast.synopses.HistogramOP
import edu.ucr.cs.bdlab.beast.synopses.PointSampleAccumulator
import edu.ucr.cs.bdlab.beast.synopses.PointSampler
import edu.ucr.cs.bdlab.beast.synopses.Summary
import edu.ucr.cs.bdlab.beast.synopses.SummaryAccumulator
import edu.ucr.cs.bdlab.beast.synopses.Synopsis
import edu.ucr.cs.bdlab.beast.util.BufferedFSDataInputStream
import edu.ucr.cs.bdlab.beast.util.FileListRDD
import edu.ucr.cs.bdlab.beast.util.KryoInputToObjectInput
import edu.ucr.cs.bdlab.beast.util.KryoOutputToObjectOutput
import edu.ucr.cs.bdlab.beast.util.LRUCache
import edu.ucr.cs.bdlab.beast.util.OperationHelper
import edu.ucr.cs.bdlab.beast.util.Parallel2
import edu.ucr.cs.bdlab.beast.util.StaticFileWebHandler
import edu.ucr.cs.bdlab.beast.util.WebUtil
import edu.ucr.cs.bdlab.beast.util.ZipUtil
import edu.ucr.cs.bdlab.davinci.DiskTileHashtable
import edu.ucr.cs.bdlab.davinci.IntermediateVectorTile
import edu.ucr.cs.bdlab.davinci.IntermediateVectorTileSerializer
import edu.ucr.cs.bdlab.davinci.LiteGeometry
import edu.ucr.cs.bdlab.davinci.LiteList
import edu.ucr.cs.bdlab.davinci.LitePolygon
import edu.ucr.cs.bdlab.davinci.MVTDataVisualizer
import edu.ucr.cs.bdlab.davinci.MultilevelPlot
import edu.ucr.cs.bdlab.davinci.SVGPlotter
import edu.ucr.cs.bdlab.davinci.SingleLevelPlot
import edu.ucr.cs.bdlab.davinci.TileCreatorFlatPartiotioning
import edu.ucr.cs.bdlab.davinci.TileCreatorPyramidPartitioning
import edu.ucr.cs.bdlab.davinci.VectorCanvas
import edu.ucr.cs.bdlab.davinci.VectorLayerBuilder
import edu.ucr.cs.bdlab.davinci.VectorTileCreatorFlatPartitioning
import edu.ucr.cs.bdlab.davinci.VisualizationHelper
import edu.ucr.cs.bdlab.davinci.VisualizationMixin
import edu.ucr.cs.bdlab.raptor.AbstractConvolutionTile
import edu.ucr.cs.bdlab.raptor.AbstractGeoTiffTile
import edu.ucr.cs.bdlab.raptor.CompactIntersectionsIterator
import edu.ucr.cs.bdlab.raptor.CompactIntersectionsTileBreaker
import edu.ucr.cs.bdlab.raptor.ConvolutionTileSerializer
import edu.ucr.cs.bdlab.raptor.EmptyTile
import edu.ucr.cs.bdlab.raptor.ExplodedTile
import edu.ucr.cs.bdlab.raptor.FilterTile
import edu.ucr.cs.bdlab.raptor.GeoTiffConstants
import edu.ucr.cs.bdlab.raptor.GeoTiffReader
import edu.ucr.cs.bdlab.raptor.GeoTiffTileDouble
import edu.ucr.cs.bdlab.raptor.GeoTiffTileDoubleArray
import edu.ucr.cs.bdlab.raptor.GeoTiffTileFloat
import edu.ucr.cs.bdlab.raptor.GeoTiffTileFloatArray
import edu.ucr.cs.bdlab.raptor.GeoTiffTileInt
import edu.ucr.cs.bdlab.raptor.GeoTiffTileIntArray
import edu.ucr.cs.bdlab.raptor.GeoTiffTileSerializer
import edu.ucr.cs.bdlab.raptor.GeoTiffWriter
import edu.ucr.cs.bdlab.raptor.HDF4Reader
import edu.ucr.cs.bdlab.raptor.HDFTile
import edu.ucr.cs.bdlab.raptor.IRasterReader
import edu.ucr.cs.bdlab.raptor.IntersectionsIterator
import edu.ucr.cs.bdlab.raptor.IntersectionsIterator1
import edu.ucr.cs.bdlab.raptor.MapPixelsTile
import edu.ucr.cs.bdlab.raptor.MaskTile
import edu.ucr.cs.bdlab.raptor.MaskTileSerializer
import edu.ucr.cs.bdlab.raptor.MemoryTile
import edu.ucr.cs.bdlab.raptor.MemoryTile2
import edu.ucr.cs.bdlab.raptor.MemoryTileSerializer
import edu.ucr.cs.bdlab.raptor.MemoryTileWindow
import edu.ucr.cs.bdlab.raptor.MemoryTileWindowSerializer
import edu.ucr.cs.bdlab.raptor.PixelIterator
import edu.ucr.cs.bdlab.raptor.PixelIterator3
import edu.ucr.cs.bdlab.raptor.PixelRange
import edu.ucr.cs.bdlab.raptor.PixelsInside
import edu.ucr.cs.bdlab.raptor.RaptorJoin
import edu.ucr.cs.bdlab.raptor.RaptorJoinFeature
import edu.ucr.cs.bdlab.raptor.RaptorJoinResult
import edu.ucr.cs.bdlab.raptor.RaptorJoinResultTile
import edu.ucr.cs.bdlab.raptor.RaptorMixin
import edu.ucr.cs.bdlab.raptor.RasterFileRDD
import edu.ucr.cs.bdlab.raptor.RasterOperationsFocal
import edu.ucr.cs.bdlab.raptor.RasterOperationsGlobal
import edu.ucr.cs.bdlab.raptor.RasterOperationsLocal
import edu.ucr.cs.bdlab.raptor.RasterPartitioner
import edu.ucr.cs.bdlab.raptor.ReshapeTile
import edu.ucr.cs.bdlab.raptor.SlidingWindowTile
import edu.ucr.cs.bdlab.raptor.StackedTile
import edu.ucr.cs.bdlab.raptor.TileIterator
import edu.ucr.cs.bdlab.raptor.ZonalStatistics
import org.apache.spark.beast.CRSServer
import org.apache.spark.beast.SparkSQLRegistration
import org.apache.spark.beast.sql.EnvelopeDataType
import org.apache.spark.beast.sql.GeometryDataType
import edu.ucr.cs.bdlab.beast._
import com.esotericsoftware.kryo.Kryo
import com.esotericsoftware.kryo.io.Input
import com.esotericsoftware.kryo.io.KryoDataOutput
import com.esotericsoftware.kryo.io.Output
import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.databind.node.ArrayNode
import com.fasterxml.jackson.databind.node.IntNode
import com.fasterxml.jackson.databind.node.NumericNode
import com.fasterxml.jackson.databind.node.TextNode
import edu.ucr.cs.bdlab.beast.cg.CGOperationsMixin._
import edu.ucr.cs.bdlab.beast.cg.Reprojector.TransformationInfo
import edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.JavaPartitionedSpatialRDD
import edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.RasterRDD
import edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.SpatialRDD
import edu.ucr.cs.bdlab.beast.cg.SpatialJoinAlgorithms.ESJDistributedAlgorithm
import edu.ucr.cs.bdlab.beast.cg.SpatialJoinAlgorithms.ESJPredicate
import edu.ucr.cs.bdlab.beast.cg.SpatialPartitioner
import edu.ucr.cs.bdlab.beast.generator.UniformDistribution
import edu.ucr.cs.bdlab.beast.generator._
import edu.ucr.cs.bdlab.beast.geolite.EmptyGeometry
import edu.ucr.cs.bdlab.beast.geolite.EnvelopeND
import edu.ucr.cs.bdlab.beast.geolite.EnvelopeNDLite
import edu.ucr.cs.bdlab.beast.geolite.GeometryHelper
import edu.ucr.cs.bdlab.beast.geolite.GeometryReader
import edu.ucr.cs.bdlab.beast.geolite.GeometryType
import edu.ucr.cs.bdlab.beast.geolite.PointND
import edu.ucr.cs.bdlab.beast.indexing.CellPartitioner
import edu.ucr.cs.bdlab.beast.indexing.GridPartitioner
import edu.ucr.cs.bdlab.beast.indexing.IndexHelper.NumPartitions
import edu.ucr.cs.bdlab.beast.io.FeatureReader
import edu.ucr.cs.bdlab.beast.io.GeoJSONFeatureWriter
import edu.ucr.cs.bdlab.beast.io.PushDownSpatialFilter
import edu.ucr.cs.bdlab.beast.io.SpatialFileRDD.FilePartition
import edu.ucr.cs.bdlab.beast.io.shapefile.DBFConstants
import edu.ucr.cs.bdlab.beast.io.shapefile.ShapefileFeatureReader
import edu.ucr.cs.bdlab.beast.io.shapefile.ShapefileGeometryWriter
import edu.ucr.cs.bdlab.beast.io.tiff.AbstractTiffTile
import edu.ucr.cs.bdlab.beast.io.tiff.TiffConstants
import edu.ucr.cs.bdlab.beast.synopses.UniformHistogram
import edu.ucr.cs.bdlab.beast.util.CompactLongArray
import edu.ucr.cs.bdlab.davinci.VectorTile.Tile
import edu.ucr.cs.bdlab.raptor.RaptorMixin.RasterReadMixinFunctions
import org.apache.commons.compress.archivers.zip.Zip64Mode
import org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream
import org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream
import org.apache.commons.io.FileUtils
import org.apache.commons.io.IOUtils
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.FileSystem
import org.apache.hadoop.fs.Path
import org.apache.hadoop.io.IOUtils.NullOutputStream
import org.apache.hadoop.mapreduce.InputSplit
import org.apache.hadoop.mapreduce.TaskAttemptContext
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat
import org.apache.hadoop.mapreduce.lib.input.FileSplit
import org.apache.hadoop.shaded.org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream
import org.apache.http.HttpEntity
import org.apache.http.client.HttpClient
import org.apache.http.client.methods.HttpPost
import org.apache.http.entity.ByteArrayEntity
import org.apache.http.impl.client.HttpClients
import org.apache.spark.SparkConf
import org.apache.spark.api.java.JavaRDD
import org.apache.spark.sql.Row
import org.apache.spark.sql.Row.empty.schema
import org.apache.spark.sql.SaveMode
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.catalyst.InternalRow
import org.apache.spark.sql.catalyst.expressions.GenericRowWithSchema
import org.apache.spark.sql.types.BooleanType
import org.apache.spark.sql.types.DoubleType
import org.apache.spark.sql.types.FloatType
import org.apache.spark.sql.types.IntegerType
import org.apache.spark.sql.types.StructField
import org.apache.spark.sql.types.StructType
import org.apache.spark.sql.types._
import org.geotools.referencing.CRS
import org.geotools.referencing.crs.DefaultGeographicCRS
import org.geotools.referencing.crs.DefaultProjectedCRS
import org.geotools.referencing.cs.DefaultCartesianCS
import org.geotools.referencing.cs.DefaultEllipsoidalCS
import org.geotools.referencing.datum.DefaultEllipsoid
import org.geotools.referencing.datum.DefaultGeodeticDatum
import org.geotools.referencing.datum.DefaultPrimeMeridian
import org.geotools.referencing.factory.OrderedAxisAuthorityFactory
import org.geotools.referencing.operation.DefaultMathTransformFactory
import org.geotools.util.factory.Hints
import org.locationtech.jts.geom.Coordinate
import org.locationtech.jts.geom.CoordinateSequence
import org.locationtech.jts.geom.CoordinateSequenceFactory
import org.locationtech.jts.geom.CoordinateXY
import org.locationtech.jts.geom.Envelope
import org.locationtech.jts.geom.Geometry
import org.locationtech.jts.geom.GeometryFactory
import org.locationtech.jts.geom.LineString
import org.locationtech.jts.geom.LinearRing
import org.locationtech.jts.geom.Polygon
import org.locationtech.jts.geom.PrecisionModel
import org.locationtech.jts.geom._
import org.locationtech.jts.io.WKTReader
import org.opengis.parameter.GeneralParameterValue
import org.opengis.referencing.crs.CoordinateReferenceSystem
import org.opengis.referencing.cs.AxisDirection
import org.opengis.referencing.operation.MathTransform
import scala.collection.JavaConverters._
import scala.collection.JavaConverters.enumerationAsScalaIteratorConverter
import scala.collection.immutable.Range
import scala.collection.mutable

// Compiled form (scalac + spark-submit --class GeoJobMain). This is the proven
// path: an implicit class like RaptorMixin's sc.geoTiff resolves when compiled
// inside an object, but NOT in the spark-shell -i REPL.
object GeoJob {
  def run(sc: SparkContext): Unit = {
    // Alias: LLM-authored snippets frequently reach for `sparkContext` (the
    // SparkSession accessor name) rather than the harness binding `sc`. Expose
    // both so a correct call doesn't fail on the binding name alone.
    val sparkContext = sc
    val spark = SparkSession.builder().getOrCreate()
    // Typed sample inputs (from comprehension.execute.sample_data). Use the
    // one(s) whose type matches the API's parameters.
    val vector_shapefile = "file:///home/zshan011/apps/aideal/studies/2026-11-17-full-rdpro/inputs/fixtures/Boston_Neighborhood_Boundaries_sample_grail.shp"
    val raster_tif = "file:///home/zshan011/apps/aideal/studies/2026-11-17-full-rdpro/inputs/fixtures/nldas_boston_30m.tif"
    val hdf_file = "file:///home/zshan011/apps/aideal/studies/2026-11-17-full-rdpro/inputs/fixtures/sample.hdf"
    val output_dir = "file:///home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/qualified-raptor/runs/original/rdpro_scala/rdpro_scala/execution/output"

    // pre-loaded typed inputs (comprehension.execute.preamble)
    // Fixed input contract shared by all conditions: the supplied GeoTIFF has11Float32bands.
    val rasterRDD: RasterRDD[Array[Float]] = sc.geoTiff[Array[Float]](raster_tif)
    val featuresRDD: RDD[IFeature] = sc.shapefile(vector_shapefile)

    // TODO API_TEST_START
    val serializer = new edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer()
    val result = serializer.isImmutable
    println(s"__CHECK__ scala:edu.ucr.cs.bdlab.beast.geolite.RasterMetadataSerializer.isImmutable $result")
    assert(result == true, "RasterMetadataSerializer is expected to be immutable by design contract")
    // TODO API_TEST_END
  }
}

object GeoJobMain {
  def main(args: Array[String]): Unit = {
    val spark = SparkSession.builder().appName("ApiTest").master("local[2]").getOrCreate()
    try {
      GeoJob.run(spark.sparkContext)
      println("__DONE__ object=GeoJob")
    } catch {
      case t: Throwable =>
        Console.err.println("__RUN_ERR__ " + t.getClass.getName + ": " + t.getMessage)
        t.printStackTrace()
        throw t
    } finally {
      spark.stop()
    }
  }
}
