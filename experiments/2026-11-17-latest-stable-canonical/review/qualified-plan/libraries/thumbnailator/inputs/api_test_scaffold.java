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
            // AIDEAL_DATA_BINDINGS

            // TODO API_TEST_START
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
