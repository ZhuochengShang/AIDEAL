import java.awt.geom.AffineTransform
import java.io.{ByteArrayInputStream, DataInputStream, ObjectInput}
import edu.ucr.cs.bdlab.beast.geolite.RasterMetadata
import org.apache.spark.beast.sql.GeometryDataType
import org.apache.spark.sql.types._

/** Public task utilities. No readType, rescale or numTiles target is called here. */
object StudySupport {
  def tagInput(values: Array[Double]): ObjectInput = {
    val bytes = values.map { value =>
      require(!value.isNaN && !value.isInfinity && value == value.toInt && value >= -128 && value <= 127,
        "Tags must be signed-byte integers")
      value.toByte
    }
    new ObjectInput {
      private val in = new DataInputStream(new ByteArrayInputStream(bytes))
      override def readObject(): AnyRef = throw new UnsupportedOperationException("Raw tags, not Java objects")
      override def read(): Int = in.read()
      override def read(b: Array[Byte]): Int = in.read(b)
      override def read(b: Array[Byte], off: Int, len: Int): Int = in.read(b, off, len)
      override def skip(n: Long): Long = in.skip(n)
      override def available(): Int = in.available()
      override def close(): Unit = in.close()
      override def readFully(b: Array[Byte]): Unit = in.readFully(b)
      override def readFully(b: Array[Byte], off: Int, len: Int): Unit = in.readFully(b, off, len)
      override def skipBytes(n: Int): Int = in.skipBytes(n)
      override def readBoolean(): Boolean = in.readBoolean()
      override def readByte(): Byte = in.readByte()
      override def readUnsignedByte(): Int = in.readUnsignedByte()
      override def readShort(): Short = in.readShort()
      override def readUnsignedShort(): Int = in.readUnsignedShort()
      override def readChar(): Char = in.readChar()
      override def readInt(): Int = in.readInt()
      override def readLong(): Long = in.readLong()
      override def readFloat(): Float = in.readFloat()
      override def readDouble(): Double = in.readDouble()
      override def readLine(): String = in.readLine()
      override def readUTF(): String = in.readUTF()
    }
  }

  def typeSummary(value: DataType): Array[Double] = {
    def ordinal(t: DataType): Int = t match {
      case ByteType => 0
      case ShortType => 1
      case IntegerType => 2
      case LongType => 3
      case FloatType => 4
      case DoubleType => 5
      case StringType => 6
      case BooleanType => 7
      case GeometryDataType => 8
      case DateType => 9
      case TimestampType => 10
      case _: MapType => 11
      case _: ArrayType => 12
      case BinaryType => -1
      case _ => throw new IllegalArgumentException("Type is outside the public tag protocol")
    }
    def visit(t: DataType, depth: Int): Array[Double] = {
      val children: Seq[DataType] = t match {
        case m: MapType => Seq(m.keyType, m.valueType)
        case a: ArrayType => Seq(a.elementType)
        case _ => Seq.empty
      }
      if (children.isEmpty) Array(1.0, depth.toDouble, 1.0, (ordinal(t) + 2.0) * depth, 0.0)
      else {
        val parts = children.map(visit(_, depth + 1))
        val nullable = t match {
          case m: MapType => if (m.valueContainsNull) 1.0 else 0.0
          case a: ArrayType => if (a.containsNull) 1.0 else 0.0
          case _ => 0.0
        }
        Array(1.0 + parts.map(_(0)).sum, parts.map(_(1)).max,
          parts.map(_(2)).sum, parts.map(_(3)).sum, nullable + parts.map(_(4)).sum)
      }
    }
    Array(ordinal(value).toDouble) ++ visit(value, 1)
  }

  def metadata(v: Array[Double]): RasterMetadata = {
    require(v.length >= 10, "Metadata needs ten public input fields")
    new RasterMetadata(v(0).toInt, v(1).toInt, v(2).toInt, v(3).toInt,
      v(4).toInt, v(5).toInt, 4326, new AffineTransform(v(6), 0.0, 0.0, v(7), v(8), v(9)))
  }

  def metadataSummary(m: RasterMetadata): Array[Double] = Array(
    m.x1.toDouble, m.y1.toDouble, m.x2.toDouble, m.y2.toDouble,
    m.tileWidth.toDouble, m.tileHeight.toDouble, m.srid.toDouble,
    m.g2m.getScaleX, m.g2m.getScaleY, m.g2m.getTranslateX, m.g2m.getTranslateY)
}
