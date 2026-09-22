import java.nio.file.Paths;

/** Independent build probe; load target classes without executing methods. */
public class ClassOrigin {
  public static void main(String[] args) throws Exception {
    for (String name : args) {
      Class<?> type = Class.forName(name, false, ClassOrigin.class.getClassLoader());
      System.out.println(name + "\t" + Paths.get(type.getProtectionDomain().getCodeSource().getLocation().toURI()));
    }
  }
}
