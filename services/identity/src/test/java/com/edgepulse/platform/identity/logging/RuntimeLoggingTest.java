package com.edgepulse.platform.identity.logging;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;

/** ADR 0027: a fresh JVM with Maven's runtime graph, without test libraries. */
class RuntimeLoggingTest {
    @Test
    void runtimeHasExactlyOneLog4jProviderAndNoReverseBridges() throws Exception {
        runProbe("providers");
    }

    @Test
    void applicationContextActivatesLog4j2WithTheRestrictedConsoleConfiguration() throws Exception {
        runProbe("context");
    }

    @Test
    void requestLogLineContainsTheInterceptorsCorrelationId() throws Exception {
        runProbe("correlation");
    }

    private void runProbe(String mode) throws Exception {
        Path target = Path.of("target");
        String runtime = Files.readString(target.resolve("runtime-classpath.txt")).trim();
        String classpath = target.resolve("classes") + File.pathSeparator
                + target.resolve("test-classes") + File.pathSeparator + runtime;
        String executable = System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java";
        Path output = target.resolve("runtime-logging-" + mode + ".log");
        Process process = new ProcessBuilder(Path.of(System.getProperty("java.home"), "bin", executable).toString(),
                "-cp", classpath, RuntimeLoggingProbe.class.getName(), mode)
                .redirectErrorStream(true).redirectOutput(output.toFile()).start();
        try {
            assertTrue(process.waitFor(45, TimeUnit.SECONDS), "runtime probe timed out: " + mode);
            String text = Files.readString(output);
            assertEquals(0, process.exitValue(), text);
            assertTrue(text.contains("SYNTHETIC-" + mode + "-passed"), text);
        } finally {
            if (process.isAlive()) {
                process.destroyForcibly();
            }
        }
    }
}
