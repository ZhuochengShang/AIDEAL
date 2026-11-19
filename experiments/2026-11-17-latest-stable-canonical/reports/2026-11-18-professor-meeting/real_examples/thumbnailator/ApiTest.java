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
    String output_dir = "/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/evaluator-correction-2026-11-18/explicit-inputs-r0/continuation/thumbnailator/generated_d1/execution/run_java_net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage--7e25aefac1397ac15ca99f5389fe8864c872975d1762ffe7aa5bab4c89328326/attempt_0001/output";

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
            java.awt.image.BufferedImage result = net.coobird.thumbnailator.Thumbnails.of(sourceImage)
                .size(16, 12)
                .asBufferedImage();

            if (result.getWidth() != 16 || result.getHeight() != 12) {
                throw new AssertionError("Thumbnail dimensions mismatch: expected 16x12, got " + result.getWidth() + "x" + result.getHeight());
            }

            int pixel = result.getRGB(8, 6);
            System.out.println("__CHECK__ java:net.coobird.thumbnailator.Thumbnails.Builder.asBufferedImage " + result.getWidth() + "x" + result.getHeight() + "@" + Integer.toHexString(pixel));
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
