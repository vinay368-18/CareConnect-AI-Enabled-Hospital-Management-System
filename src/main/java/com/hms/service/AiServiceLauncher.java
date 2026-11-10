package com.hms.service;

import com.hms.util.AppConfig;

import jakarta.servlet.ServletContextEvent;
import jakarta.servlet.ServletContextListener;

import java.io.File;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * Starts the Python AI microservice together with the web application and
 * stops it again when the application (or Tomcat) shuts down, so the whole
 * system runs as one application from one Tomcat.
 *
 * Behaviour:
 *  - If an AI service already answers on HMS_AI_API_URL, it is reused and
 *    left running on shutdown (it was started by someone else).
 *  - Otherwise "python api_server.py" is launched in the service folder.
 *    Startup is asynchronous: Tomcat does not wait for the models to load;
 *    the CVD pages show "AI offline" until the service reports healthy.
 *  - Its output goes to the same console as Tomcat, prefixed by uvicorn's
 *    own log format.
 *
 * Settings (environment variable, -D property, or careconnect.env):
 *  HMS_AI_AUTOSTART    "false" to disable (default: true)
 *  HMS_AI_SERVICE_DIR  folder containing api_server.py (auto-detected if unset)
 *  HMS_AI_PYTHON       Python executable (auto-detected if unset)
 *
 * Registered in WEB-INF/web.xml.
 */
public class AiServiceLauncher implements ServletContextListener {

    private static final String TAG = "[AI Service] ";
    private static final int READY_TIMEOUT_SECONDS = 180;

    private volatile Process process;
    private volatile boolean stopping;
    private Thread shutdownHook;

    @Override
    public void contextInitialized(ServletContextEvent sce) {
        String autostart = AppConfig.getOrDefault("HMS_AI_AUTOSTART", "hms.ai.autostart", "true");
        if ("false".equalsIgnoreCase(autostart) || "0".equals(autostart) || "no".equalsIgnoreCase(autostart)) {
            log("Autostart disabled (HMS_AI_AUTOSTART=" + autostart + "). Start the AI service yourself.");
            return;
        }

        String baseUrl = AppConfig.getOrDefault("HMS_AI_API_URL", "hms.ai.api.url", "http://127.0.0.1:5000");
        if (isUp(baseUrl)) {
            log("Already running at " + baseUrl + "; using it.");
            return;
        }

        Path serviceDir = findServiceDir(sce);
        if (serviceDir == null) {
            log("Not started: could not find the cvd-ai-service folder (api_server.py). "
                    + "Set HMS_AI_SERVICE_DIR in careconnect.env. The rest of the application works; "
                    + "CVD screening will show 'AI offline'.");
            return;
        }

        String python = findPython(serviceDir);
        List<String> command = new ArrayList<>();
        command.add(python);
        command.add("-u");               // unbuffered, so its log lines appear immediately
        command.add("api_server.py");

        ProcessBuilder pb = new ProcessBuilder(command);
        pb.directory(serviceDir.toFile());
        pb.inheritIO();
        pb.redirectInput(ProcessBuilder.Redirect.PIPE);   // never read Tomcat's console input

        // Hand the shared settings to the child explicitly, so both sides use
        // the same key even when they come from a -D property.
        Map<String, String> env = pb.environment();
        passThrough(env, "HMS_AI_API_KEY", "hms.ai.api.key");
        passThrough(env, "HMS_AI_API_URL", "hms.ai.api.url");
        passThrough(env, "HMS_CORS_ORIGINS", null);
        env.put("PYTHONIOENCODING", "utf-8");

        try {
            process = pb.start();
        } catch (Exception e) {
            log("Not started: could not run '" + python + "' (" + e.getMessage() + "). "
                    + "Install Python 3.10-3.12 or set HMS_AI_PYTHON in careconnect.env.");
            return;
        }
        log("Starting " + python + " api_server.py in " + serviceDir + " (pid " + process.pid() + ")");

        Thread watcher = new Thread(() -> waitUntilReady(baseUrl), "ai-service-watcher");
        watcher.setDaemon(true);
        watcher.start();

        // If the JVM is stopped without a clean webapp shutdown, still stop the child.
        try {
            shutdownHook = new Thread(this::stopProcess, "ai-service-shutdown");
            Runtime.getRuntime().addShutdownHook(shutdownHook);
        } catch (IllegalStateException ignored) {
            shutdownHook = null; // JVM already shutting down
        }
    }

    @Override
    public void contextDestroyed(ServletContextEvent sce) {
        stopProcess();
        // Unregister the hook so a redeploy does not keep the old webapp in memory.
        if (shutdownHook != null) {
            try {
                Runtime.getRuntime().removeShutdownHook(shutdownHook);
            } catch (IllegalStateException ignored) {
                // JVM already shutting down; the hook runs harmlessly
            }
            shutdownHook = null;
        }
    }

    // ------------------------------------------------------------------------

    private synchronized void stopProcess() {
        Process p = process;
        if (p == null) {
            return;
        }
        stopping = true;
        process = null;
        if (!p.isAlive()) {
            return;
        }
        log("Stopping (pid " + p.pid() + ")...");
        p.descendants().forEach(ProcessHandle::destroy);
        p.destroy();
        try {
            if (!p.waitFor(10, TimeUnit.SECONDS)) {
                p.descendants().forEach(ProcessHandle::destroyForcibly);
                p.destroyForcibly();
                p.waitFor(5, TimeUnit.SECONDS);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        log("Stopped.");
    }

    private void waitUntilReady(String baseUrl) {
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(READY_TIMEOUT_SECONDS);
        while (System.nanoTime() < deadline) {
            Process p = process;
            if (p == null || stopping) {
                return;
            }
            if (!p.isAlive()) {
                log("Exited early with code " + p.exitValue() + ". See the Python messages above. "
                        + "Common causes: missing packages (pip install -r cvd-ai-service/requirements.txt), "
                        + "port already in use, or missing model files in cvd-ai-service/models.");
                return;
            }
            if (isUp(baseUrl)) {
                log("Ready at " + baseUrl);
                return;
            }
            sleep(2000);
        }
        log("Still not answering at " + baseUrl + " after " + READY_TIMEOUT_SECONDS
                + "s; leaving it running. Check the Python messages above.");
    }

    /** True when something answers 200 on /health (healthy or degraded). */
    private static boolean isUp(String baseUrl) {
        try {
            HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).build();
            HttpRequest req = HttpRequest.newBuilder(URI.create(stripSlash(baseUrl) + "/health"))
                    .timeout(Duration.ofSeconds(3)).GET().build();
            HttpResponse<Void> resp = client.send(req, HttpResponse.BodyHandlers.discarding());
            return resp.statusCode() == 200;
        } catch (Exception e) {
            return false;
        }
    }

    private static Path findServiceDir(ServletContextEvent sce) {
        List<Path> candidates = new ArrayList<>();
        String configured = AppConfig.get("HMS_AI_SERVICE_DIR", "hms.ai.service.dir");
        if (configured != null && !configured.isEmpty()) {
            candidates.add(Paths.get(configured));
        }
        // Running straight from the project (e.g. an IDE that serves src/main/webapp)
        String webRoot = sce.getServletContext().getRealPath("/");
        if (webRoot != null) {
            Path p = Paths.get(webRoot).toAbsolutePath();
            for (int i = 0; i < 4 && p != null; i++) {
                candidates.add(p.resolve("cvd-ai-service"));
                p = p.getParent();
            }
        }
        candidates.add(Paths.get(System.getProperty("user.dir"), "cvd-ai-service"));
        for (Path c : candidates) {
            if (Files.isRegularFile(c.resolve("api_server.py"))) {
                return c.toAbsolutePath().normalize();
            }
        }
        return null;
    }

    private static String findPython(Path serviceDir) {
        String configured = AppConfig.get("HMS_AI_PYTHON", "hms.ai.python");
        if (configured != null && !configured.isEmpty()) {
            return configured;
        }
        boolean windows = System.getProperty("os.name", "").toLowerCase().contains("win");
        String exe = windows ? "Scripts" + File.separator + "python.exe" : "bin" + File.separator + "python";
        List<Path> venvs = new ArrayList<>();
        venvs.add(serviceDir.resolve(".venv"));
        venvs.add(serviceDir.resolve("venv"));
        String home = System.getProperty("user.home");
        if (home != null) {
            venvs.add(Paths.get(home, "cvd-env"));
        }
        for (Path v : venvs) {
            Path py = v.resolve(exe);
            if (Files.isRegularFile(py)) {
                return py.toString();
            }
        }
        return windows ? "python" : "python3";
    }

    private static void passThrough(Map<String, String> env, String name, String prop) {
        String v = AppConfig.get(name, prop);
        if (v != null && !v.isEmpty()) {
            env.put(name, v);
        }
    }

    private static String stripSlash(String s) {
        return s.endsWith("/") ? s.substring(0, s.length() - 1) : s;
    }

    private static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private static void log(String msg) {
        System.out.println(TAG + msg);
    }
}
