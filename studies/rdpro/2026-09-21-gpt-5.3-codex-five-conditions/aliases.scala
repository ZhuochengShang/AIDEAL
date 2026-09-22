package edu.ucr.cs.bdlab.beast.geolite

import java.io.ObjectInput
import org.apache.spark.sql.types.DataType

object AidealAliases0001 {

  def featureReadType(in: ObjectInput): DataType =
    Feature.readType(in)

  def rasterSchemaReadType(in: ObjectInput): DataType =
    RasterSchemaHelper.readType(in)

  def numTilesOf(metadata: RasterMetadata): Int =
    metadata.numTiles

  def rescaleTo(metadata: RasterMetadata, newRasterWidth: Int, newRasterHeight: Int): RasterMetadata =
    metadata.rescale(newRasterWidth, newRasterHeight)
}
