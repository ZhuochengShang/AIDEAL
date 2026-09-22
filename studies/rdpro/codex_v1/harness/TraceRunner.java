import com.sun.jdi.*;
import com.sun.jdi.connect.*;
import com.sun.jdi.event.*;
import com.sun.jdi.request.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Parent-side runtime call observation. Generated code cannot manufacture events. */
public class TraceRunner {
  private static final Map<String, String> TARGETS = Map.of(
    "Feature$.readType", "(Ljava/io/ObjectInput;)Lorg/apache/spark/sql/types/DataType;",
    "RasterSchemaHelper$.readType", "(Ljava/io/ObjectInput;)Lorg/apache/spark/sql/types/DataType;",
    "RasterMetadata.rescale", "(II)Ledu/ucr/cs/bdlab/beast/geolite/RasterMetadata;",
    "RasterMetadata.numTiles", "()I");
  public static void main(String[] args) throws Exception {
    LaunchingConnector connector = Bootstrap.virtualMachineManager().defaultConnector();
    Map<String, Connector.Argument> options = connector.defaultArguments();
    options.get("main").setValue("Harness " + args[1]);
    options.get("options").setValue("-Djava.security.manager=allow -Xlog:class+load=info:file=classload.log -cp \"" + args[0] + "\"");
    VirtualMachine vm = connector.launch(options);
    Process child = vm.process();
    Runtime.getRuntime().addShutdownHook(new Thread(() -> child.destroyForcibly()));
    Thread out = pump(child.getInputStream(), "program.stdout");
    Thread err = pump(child.getErrorStream(), "program.stderr");
    for (String target : new String[]{"RasterMetadata", "RasterSchemaHelper$", "Feature$"}) {
      ClassPrepareRequest request = vm.eventRequestManager().createClassPrepareRequest();
      request.addClassFilter("edu.ucr.cs.bdlab.beast.geolite." + target);
      request.setSuspendPolicy(EventRequest.SUSPEND_ALL);
      request.enable();
    }
    Set<String> entered = new TreeSet<>();
    boolean running = true;
    while (running) {
      try {
        EventSet events = vm.eventQueue().remove();
        for (Event event : events) {
          if (event instanceof ClassPrepareEvent) {
            ReferenceType type = ((ClassPrepareEvent)event).referenceType();
            for (Method method : type.methods()) {
              String key = type.name().substring(type.name().lastIndexOf('.') + 1) + "." + method.name();
              if (method.signature().equals(TARGETS.get(key))) {
                BreakpointRequest point = vm.eventRequestManager().createBreakpointRequest(method.location());
                point.setSuspendPolicy(EventRequest.SUSPEND_NONE);
                point.enable();
              }
            }
          }
          if (event instanceof BreakpointEvent) {
            Method method = ((BreakpointEvent)event).location().method();
            entered.add(method.declaringType().name() + "." + method.name() + method.signature());
          }
          if (event instanceof VMDeathEvent || event instanceof VMDisconnectEvent) running = false;
        }
        events.resume();
      } catch (VMDisconnectedException ex) { running = false; }
    }
    int exit = child.waitFor();
    out.join(); err.join();
    Files.write(Paths.get("trace.txt"), entered);
    System.exit(exit);
  }
  private static Thread pump(InputStream input, String file) {
    Thread thread = new Thread(() -> {
      try { Files.copy(input, Paths.get(file)); }
      catch (IOException ex) { throw new RuntimeException(ex); }
    });
    thread.start();
    return thread;
  }
}
