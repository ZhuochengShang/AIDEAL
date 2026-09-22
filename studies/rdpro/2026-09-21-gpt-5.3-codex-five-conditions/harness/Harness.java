import java.security.Permission;
import java.util.*;

/** Load untrusted Solution only after restricting I/O, process, and runtime changes. */
public class Harness {
  public static void main(String[] args) throws Exception {
    final String[] roots = System.getProperty("java.class.path").split(java.io.File.pathSeparator);
    final String javaHome = System.getProperty("java.home");
    // Initialize path normalization before installing the permission callback.
    java.nio.file.Paths.get(javaHome).toAbsolutePath().normalize();
    List<double[]> inputs = new ArrayList<>();
    for (String vector : args[0].split(";"))
      inputs.add(Arrays.stream(vector.split(",")).mapToDouble(Double::parseDouble).toArray());
    System.setSecurityManager(new SecurityManager() {
      public void checkPermission(Permission p) {
        String name = p.getName();
        if (p instanceof java.io.FilePermission) {
          if (!p.getActions().equals("read")) throw new SecurityException("File writes denied");
          name = java.nio.file.Paths.get(name).toAbsolutePath().normalize().toString();
          boolean allowed = name.startsWith(javaHome + "/");
          for (String root : roots) allowed |= name.equals(root) || (!root.endsWith(".jar") && name.startsWith(root + "/"));
          if (!allowed) throw new SecurityException("File access outside runtime denied");
        }
        if (p instanceof java.net.SocketPermission) throw new SecurityException("Network denied");
        if (p instanceof RuntimePermission && (name.equals("setSecurityManager") || name.startsWith("exitVM")
            || name.startsWith("loadLibrary") || name.equals("createClassLoader") || name.startsWith("getenv")
            || name.equals("setIO") || name.equals("setContextClassLoader")))
          throw new SecurityException("Runtime mutation denied");
        if (p instanceof java.lang.reflect.ReflectPermission) {
          boolean lambdaBootstrap = false;
          for (Class<?> caller : getClassContext())
            lambdaBootstrap |= caller.getName().startsWith("java.lang.invoke.InnerClassLambdaMetafactory");
          if (!lambdaBootstrap) throw new SecurityException("Reflection override denied");
        }
        if (p instanceof java.util.PropertyPermission && p.getActions().contains("write"))
          throw new SecurityException("Property mutation denied");
      }
      public void checkExec(String command) { throw new SecurityException("Process execution denied"); }
    });
    for (double[] input : inputs) {
      double[] result = Solution.solve(input);
      System.out.println("AIDEAL_RESULT=" + Arrays.toString(result));
    }
  }
}
