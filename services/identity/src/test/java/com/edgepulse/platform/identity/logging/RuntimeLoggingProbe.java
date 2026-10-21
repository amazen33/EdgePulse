package com.edgepulse.platform.identity.logging;

import com.edgepulse.platform.identity.IdentityServiceApplication;
import com.edgepulse.platform.identity.adapter.in.rest.CorrelationIdHandlerInterceptor;
import com.edgepulse.platform.identity.correlation.CorrelationIdConstants;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.PrintStream;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.ServiceLoader;
import java.util.Set;
import java.util.stream.Collectors;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.core.LoggerContext;
import org.apache.logging.log4j.core.appender.ConsoleAppender;
import org.apache.logging.log4j.core.net.JndiManager;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.slf4j.spi.SLF4JServiceProvider;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.logging.LoggingSystem;
import org.springframework.boot.logging.log4j2.Log4J2LoggingSystem;

/** Test launcher only. This class has no dependency on JUnit, Mockito or Spring Test. */
public final class RuntimeLoggingProbe {
    private RuntimeLoggingProbe() { }

    public static void main(String[] args) throws Exception {
        String mode = args[0];
        if (mode.equals("providers")) {
            verifyProvider();
        } else {
            try (var application = new SpringApplicationBuilder(IdentityServiceApplication.class).run(
                    "--spring.main.web-application-type=none", "--edgepulse.identity.grpc.enabled=false",
                    "--logging.config=classpath:log4j2-spring.xml")) {
                require(LoggingSystem.get(application.getClassLoader()) instanceof Log4J2LoggingSystem,
                        "Boot must select its Log4j 2 logging system");
                var configuration = ((LoggerContext) LogManager.getContext(false)).getConfiguration();
                require(configuration.getConfigurationSource().getLocation().endsWith("log4j2-spring.xml"),
                        "the service's explicit configuration must be active");
                require(configuration.getAppenders().size() == 1
                        && configuration.getAppender("CONSOLE") instanceof ConsoleAppender,
                        "only the console appender is permitted");
                require(!JndiManager.isJndiLookupEnabled(), "JNDI lookups must be disabled");
                if (mode.equals("correlation")) {
                    verifyRequestLine();
                } else {
                    require(mode.equals("context"), "unknown probe mode");
                }
            }
        }
        System.out.println("SYNTHETIC-" + mode + "-passed");
    }

    private static void verifyProvider() throws Exception {
        var providers = ServiceLoader.load(SLF4JServiceProvider.class).stream().toList();
        require(providers.size() == 1, "exactly one runtime SLF4J provider is required");
        require(providers.get(0).type().getName().equals("org.apache.logging.slf4j.SLF4JServiceProvider"),
                "the provider must be Log4j 2's");
        Set<String> jars = Arrays.stream(System.getProperty("java.class.path").split(File.pathSeparator))
                .map(p -> Path.of(p).getFileName().toString()).collect(Collectors.toSet());
        Set<String> log4j = jars.stream().filter(n -> n.startsWith("log4j-")).collect(Collectors.toSet());
        require(log4j.equals(Set.of("log4j-api-2.26.1.jar", "log4j-core-2.26.1.jar",
                "log4j-jul-2.26.1.jar", "log4j-slf4j2-impl-2.26.1.jar")), "one exact four-artifact Log4j set");
        require(jars.stream().noneMatch(n -> n.startsWith("logback-") || n.startsWith("jul-to-slf4j-")
                || n.startsWith("spring-boot-starter-log4j2-") || n.startsWith("spring-boot-starter-logging-")),
                "no Logback, reverse bridges or logging starter may be runtime-reachable");
        require(jars.stream().noneMatch(n -> n.startsWith("junit-") || n.startsWith("mockito-")),
                "the provider proof must not use the test dependency classpath");
        require(LoggerFactory.getILoggerFactory().getClass().getName()
                .equals("org.apache.logging.slf4j.Log4jLoggerFactory"), "the selected factory must be Log4j 2");
    }

    private static void verifyRequestLine() throws Exception {
        var interceptor = new CorrelationIdHandlerInterceptor();
        Map<String, String> headers = new HashMap<>();
        var request = (HttpServletRequest) Proxy.newProxyInstance(RuntimeLoggingProbe.class.getClassLoader(),
                new Class<?>[]{HttpServletRequest.class}, (proxy, method, args) -> null);
        var response = (HttpServletResponse) Proxy.newProxyInstance(RuntimeLoggingProbe.class.getClassLoader(),
                new Class<?>[]{HttpServletResponse.class}, (proxy, method, args) -> {
                    if (method.getName().equals("setHeader")) {
                        headers.put((String) args[0], (String) args[1]);
                    }
                    return null;
                });
        PrintStream original = System.out;
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (PrintStream captured = new PrintStream(bytes, true, StandardCharsets.UTF_8)) {
            System.setOut(captured);
            interceptor.preHandle(request, response, new Object());
            String correlation = headers.get(CorrelationIdConstants.HTTP_HEADER);
            require(correlation != null && correlation.equals(MDC.get(CorrelationIdConstants.MDC_KEY)),
                    "the request header and MDC must share the server-issued correlation ID");
            LoggerFactory.getLogger("SYNTHETIC-request").info("SYNTHETIC-request-line");
            String line = bytes.toString(StandardCharsets.UTF_8);
            require(line.contains("[" + correlation + "]") && line.contains("SYNTHETIC-request-line"),
                    "the actual console request line must include its correlation ID");
        } finally {
            interceptor.afterCompletion(request, response, new Object(), null);
            System.setOut(original);
        }
        require(MDC.get(CorrelationIdConstants.MDC_KEY) == null, "request completion must clear the MDC");
    }

    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
