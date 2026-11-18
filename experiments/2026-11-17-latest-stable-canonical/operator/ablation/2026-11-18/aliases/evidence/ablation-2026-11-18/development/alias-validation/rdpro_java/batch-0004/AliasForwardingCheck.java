import edu.ucr.cs.bdlab.raptor.*;
import edu.ucr.cs.bdlab.beast.io.tiff.ITiffReader;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
public class AliasForwardingCheck {
  public static void main(String[] args) throws Exception {
    for (int i=0; i<2; i++) {
      Path path = new Path(args[i]);
      try (ITiffReader reader = ITiffReader.openFile(path.getFileSystem(new Configuration()), path)) {
        GeoTiffMetadata metadata = new GeoTiffMetadata(reader, reader.getLayer(0));
        boolean expected = i==1;
        boolean original = metadata.hasModelTrasformation();
        boolean alias = AidealJavaAliases0004.hasModelTransformation(metadata);
        if (original != expected || alias != original) throw new AssertionError("Forwarding mismatch");
        if (metadata.hasModelTrasformation() != original) throw new AssertionError("Mutation");
        System.out.println("fixture="+i+" original="+original+" alias="+alias);
      }
    }
    GeoTiffMetadata absent = null;
    String originalError=null, aliasError=null;
    try { absent.hasModelTrasformation(); } catch (Exception e) {originalError=e.getClass().getName();}
    try { AidealJavaAliases0004.hasModelTransformation(absent); } catch (Exception e) {aliasError=e.getClass().getName();}
    if (!"java.lang.NullPointerException".equals(originalError) || !originalError.equals(aliasError))
      throw new AssertionError("Null receiver behavior changed");
    System.out.println("null_receiver="+aliasError);
    System.out.println("FORWARDING_CHECK_PASSED");
  }
}
