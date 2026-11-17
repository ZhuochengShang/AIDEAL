import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;

import javax.imageio.ImageIO;

import net.coobird.thumbnailator.*;
import net.coobird.thumbnailator.builders.*;
import net.coobird.thumbnailator.filters.*;
import net.coobird.thumbnailator.geometry.*;
import net.coobird.thumbnailator.makers.*;
import net.coobird.thumbnailator.name.*;
import net.coobird.thumbnailator.resizers.*;
import net.coobird.thumbnailator.resizers.configurations.*;
import net.coobird.thumbnailator.tasks.*;
import net.coobird.thumbnailator.tasks.io.*;
import net.coobird.thumbnailator.util.*;
import net.coobird.thumbnailator.util.exif.*;

public final class ApiTest {
    private ApiTest() {}

    public static void main(String[] args) {
        try {
            String grid_png = "/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/thumbnailator/src/test/resources/Thumbnailator/grid.png";
    String grid_jpeg = "/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/thumbnailator/src/test/resources/Thumbnailator/grid.jpg";
    String exif_jpeg = "/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/sources/thumbnailator/src/test/resources/Exif/original.jpg";
    String output_dir = "/home/zshan011/apps/aideal/checks/2026-11-17-latest-stable-runtime/native-controls/thumbnailator/output";

    // pre-loaded typed inputs (comprehension.execute.preamble)
    BufferedImage sourceImage = new BufferedImage(32, 24, BufferedImage.TYPE_INT_RGB);
    Graphics2D graphics = sourceImage.createGraphics();
    graphics.setColor(Color.BLUE);
    graphics.fillRect(0, 0, 32, 24);
    graphics.setColor(Color.YELLOW);
    graphics.fillRect(8, 6, 16, 12);
    graphics.dispose();
    BufferedImage destinationImage = new BufferedImage(16, 12, BufferedImage.TYPE_INT_RGB);
    ByteArrayOutputStream imageBytes = new ByteArrayOutputStream();
    Path outputPath = Paths.get(output_dir, "thumbnail.png");
    Files.createDirectories(outputPath.getParent());

            // TODO API_TEST_START
            net.coobird.thumbnailator.resizers.ProgressiveBilinearResizer selectedResizer =
                new net.coobird.thumbnailator.resizers.ProgressiveBilinearResizer();
            selectedResizer.resize(sourceImage, destinationImage);
            String loadedJar = selectedResizer.getClass().getProtectionDomain().getCodeSource().getLocation().getPath();
            System.out.println("__ARTIFACT__ " + loadedJar);
            if (!loadedJar.endsWith("/runtime/jars/thumbnailator-0.4.21.jar"))
                throw new AssertionError("Unexpected runtime artifact: " + loadedJar);
            if (destinationImage.getWidth() != 16 || destinationImage.getHeight() != 12)
                throw new AssertionError("Unexpected target dimensions");
            int corner = destinationImage.getRGB(0, 0) & 0xFFFFFF;
            int center = destinationImage.getRGB(8, 6) & 0xFFFFFF;
            if (destinationImage.getWidth() != 999)
                throw new AssertionError("INTENTIONAL_NEGATIVE_CONTROL width must not be 999");
            System.out.println("__CHECK__ resize unreachable-negative");
            // TODO API_TEST_END
            System.out.println("__DONE__");
        } catch (Throwable exc) {
            System.err.println("__RUN_ERR__ " + exc.getClass().getSimpleName()
                    + ": " + exc.getMessage());
            exc.printStackTrace(System.err);
            System.exit(1);
        }
    }
}
