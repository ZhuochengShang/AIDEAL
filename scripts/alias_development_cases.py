"""New standalone development examples; no held-out bank/reference/oracle input.

Two separate JVMs run each program (canonical then alias). Observations include
selected values/structures, stream state, mutations and exception classes. These
are bounded examples, never a proof of equivalence for all inputs.
"""
from alias_forwarders import alias_call, ReviewRequired


PREAMBLE = r'''
import java.io._
import java.awt.geom.{AffineTransform, Point2D}
import org.apache.spark.sql.types._
import org.apache.spark.sql.Row
import edu.ucr.cs.bdlab.beast.geolite._

object AliasDevelopmentProbe {
  def attempt(f: => String): String = try { "ok:" + f } catch {
    case e: Exception => "exception:" + e.getClass.getName
  }
  def hex(b: Array[Byte]): String = b.map(x => f"${x & 255}%02x").mkString
  def metadata(variant: Int): RasterMetadata = {
    val tx = if (variant == 1) new AffineTransform(1.2,0.4,-0.3,2.1,-7.0,11.0)
             else if (variant == 2) new AffineTransform(0.0,0.0,0.0,0.0,5.0,9.0)
             else new AffineTransform(2.5,0.0,0.0,-1.75,101.25,64.5)
    new RasterMetadata(-2,4,17,18,6,5,3857,tx)
  }
  def meta(m: RasterMetadata): String = {
    val t = new Array[Double](6); m.g2m.getMatrix(t)
    Seq(m.x1,m.y1,m.x2,m.y2,m.tileWidth,m.tileHeight,m.srid).mkString(",") + ":" + t.mkString(",")
  }
  def row(r: Row): String = r.schema.json + ":" + r.toSeq.map(x => String.valueOf(x)).mkString("|")
  def freshFeature(): Feature = new Feature(Array[Any](11,"anchor"),
    StructType(Array(StructField("count",IntegerType),StructField("label",StringType))))
  def quote(s: String): String = "\"" + s.flatMap {
    case '\\' => "\\\\"; case '"' => "\\\""; case '\n' => "\\n"
    case '\r' => "\\r"; case '\t' => "\\t"
    case c if c < ' ' => "\\u%04x".format(c.toInt)
    case c => c.toString
  } + "\""
'''


def program(certificate):
    """Build a fixed local development program for one of the supported 16 APIs."""
    api = certificate['canonical_api']; method = api.rsplit('.', 1)[1]
    owner = api.rsplit('.', 1)[0]
    def call(arguments, receiver=None, property=False):
        canonical = (receiver or owner) + '.' + method
        if not property: canonical += '(' + ', '.join(arguments) + ')'
        alias = alias_call(certificate, arguments, receiver)
        return '(if (useAlias) ' + alias + ' else ' + canonical + ')'
    cases = []
    if owner.endswith('.Feature') and method in ('readType', 'writeType'):
        for typ in ('IntegerType', 'MapType(StringType,ArrayType(LongType,true),true)', 'BinaryType'):
            setup = 'val kind: DataType = ' + typ + '; val bytes = new ByteArrayOutputStream(); val out = new ObjectOutputStream(bytes);'
            if method == 'readType':
                setup += 'Feature.writeType(kind,out); out.writeInt(197); out.flush(); val in = new ObjectInputStream(new ByteArrayInputStream(bytes.toByteArray));'
                body = 'val observed = attempt { ' + call(['in']) + '.json }; observed + ":sentinel:" + attempt { in.readInt().toString } + ":remaining:" + in.available()'
            else:
                body = 'val observed = attempt { ' + call(['kind', 'out']) + '; "unit" }; out.writeInt(197); out.flush(); observed + ":bytes:" + hex(bytes.toByteArray)'
            cases.append(setup + body)
        if method == 'readType':
            cases.append('val bytes = new ByteArrayOutputStream(); val out = new ObjectOutputStream(bytes);out.flush();val in = new ObjectInputStream(new ByteArrayInputStream(bytes.toByteArray)); attempt { ' + call(['in']) + '.json } + ":remaining:" + in.available()')
    elif owner.endswith('.Feature') and method in ('readValue', 'writeValue'):
        for typ, value, writer in [('IntegerType', '23', 'writeInt(23)'), ('DoubleType', '-4.75', 'writeDouble(-4.75)'), ('StringType', '"development-value"', 'writeUTF("development-value")')]:
            setup = 'val kind: DataType = ' + typ + '; val value: Any = ' + value + '; val bytes = new ByteArrayOutputStream(); val out = new ObjectOutputStream(bytes);'
            if method == 'readValue':
                setup += 'out.' + writer + ';out.writeInt(197);out.flush();val in = new ObjectInputStream(new ByteArrayInputStream(bytes.toByteArray));'
                body = 'val observed = attempt { String.valueOf(' + call(['in', 'kind']) + ') }; observed + ":sentinel:" + attempt { in.readInt().toString } + ":remaining:" + in.available()'
            else:
                body = 'val observed = attempt { ' + call(['out', 'value', 'kind']) + '; "unit" };out.writeInt(197);out.flush(); observed + ":bytes:" + hex(bytes.toByteArray)'
            cases.append(setup + body)
    elif owner.endswith('.Feature') and method == 'append':
        for value, typ in [('37','IntegerType'), ('2.875','DoubleType'), ('null','StringType')]:
            cases.append('val f = freshFeature(); val before = row(f); val value: Any = ' + value + '; val kind: DataType = ' + typ + '; val name = "added"; val observed = attempt { val result = ' + call(['f','value','name','kind']) + '; row(result) + ":same:" + (result eq f) }; observed + ":before:" + before + ":after:" + row(f)')
    elif owner.endswith('.Feature') and method == 'concat':
        for tail in ('"tail-A"','"tail-B"','""'):
            cases.append('val f = freshFeature(); val right = new Feature(Array[Any](' + tail + ',true),StructType(Array(StructField("suffix",StringType),StructField("flag",BooleanType))));val before = row(f) + ":" + row(right);val observed = attempt { val result = ' + call(['f','right']) + ';row(result) + ":same:" + (result eq f) };observed + ":before:" + before + ":after:" + row(f) + ":" + row(right)')
    elif owner.endswith('.RasterSchemaHelper') and method == 'detectType':
        for value in ('new java.math.BigDecimal("12.340")', 'Map("k" -> 4)', 'Array[Byte](1,4,9)', 'null'):
            cases.append('val value: Any = ' + value + '; attempt { ' + call(['value']) + '.json }')
    elif owner.endswith('.RasterSchemaHelper') and method == 'inferSchema':
        for values in ('Array[Any](31,"fresh",null)', 'Array[Any](Map("k"->7),Array[Byte](3,8),new java.math.BigDecimal("6.250"))'):
            cases.append('val values = ' + values + ';val names = Array("alpha","beta","gamma");val before = names.mkString("|");val observed = attempt { ' + call(['names','values']) + '.json };observed + ":names:" + names.mkString("|") + ":before:" + before')
    elif owner.endswith('.RasterMetadata'):
        for variant in (0,1,2):
            setup = 'val m = metadata(' + str(variant) + ');val before = meta(m);'
            if method == 'rescale':
                setup += 'val width = ' + str([13,1,27][variant]) + ';val height = ' + str([9,1,31][variant]) + ';'
                body = 'val observed = attempt { val result = ' + call(['width','height'],'m') + ';meta(result) + ":same:" + (result eq m) };'
            elif method == 'numTiles': body = 'val observed = attempt { ' + call([],'m',True) + '.toString };'
            elif method in ('getTileIDAtPixel','isPixelInRange'):
                setup += 'val x = ' + str([-2,16,17][variant]) + ';val y = ' + str([4,17,18][variant]) + ';'
                body = 'val observed = attempt { ' + call(['x','y'],'m') + '.toString };'
            elif method == 'getTileIDAtPoint':
                setup += 'val point = new Point2D.Double(7.25,8.5);m.g2m.transform(point,point);val x = point.x;val y = point.y;'
                body = 'val observed = attempt { ' + call(['x','y'],'m') + '.toString };'
            elif method in ('gridToModel','modelToGrid'):
                setup += 'val x = 7.25;val y = 8.5;val point = new Point2D.Double(123.0,-321.0);'
                body = 'val outcome = attempt { ' + call(['x','y','point'],'m') + ';"unit" };val observed = outcome + ":point:" + point.x + "," + point.y;'
            elif method == 'envelope':
                body = 'val observed = attempt { val e = ' + call([],'m',True) + ';Seq(e.getMinX,e.getMaxX,e.getMinY,e.getMaxY).mkString(",") };'
            else: raise ReviewRequired('No independent development case for ' + api)
            cases.append(setup + body + 'observed + ":before:" + before + ":after:" + meta(m)')
    else: raise ReviewRequired('No independent development case for ' + api)
    lines = [PREAMBLE, '  def main(args: Array[String]): Unit = {',
             '    require(args.length == 1 && Set("canonical","alias").contains(args(0)))',
             '    val useAlias = args(0) == "alias"', '    val observations = Seq(']
    lines += ['      { ' + case + ' }' + (',' if i < len(cases)-1 else '') for i,case in enumerate(cases)]
    lines += ['    )', '    println("AIDEAL_DEVELOPMENT_PROBE={\\"mode\\":" + quote(args(0)) + ",\\"observations\\":[" + observations.map(quote).mkString(",") + "]}")', '  }', '}', '']
    return '\n'.join(lines), len(cases)
