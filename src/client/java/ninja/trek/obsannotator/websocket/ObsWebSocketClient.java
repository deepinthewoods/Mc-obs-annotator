package ninja.trek.obsannotator.websocket;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import ninja.trek.obsannotator.config.ObsAnnotatorConfig;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;

import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.UUID;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class ObsWebSocketClient extends WebSocketClient {
    private static final Gson GSON = new Gson();
    private static final int INITIAL_RECONNECT_DELAY_MS = 2000; // 2 seconds
    private static final int MAX_RECONNECT_DELAY_MS = 60000; // 60 seconds
    private static final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);

    private final ObsAnnotatorConfig config;
    private boolean authenticated = false;
    private int reconnectAttempts = 0;
    private ScheduledFuture<?> reconnectTask = null;
    private ReconnectCallback reconnectCallback = null;

    public interface ReconnectCallback {
        void onReconnect();
    }

    public ObsWebSocketClient(ObsAnnotatorConfig config) throws Exception {
        super(new URI("ws://" + config.obsHost + ":" + config.obsPort));
        this.config = config;
        this.setConnectionLostTimeout(10);
    }

    public void setReconnectCallback(ReconnectCallback callback) {
        this.reconnectCallback = callback;
    }

    @Override
    public void onOpen(ServerHandshake handshake) {
        System.out.println("[OBS Annotator] Connected to OBS WebSocket");
        reconnectAttempts = 0; // Reset reconnect attempts on successful connection
    }

    @Override
    public void onMessage(String message) {
        try {
            JsonObject msg = GSON.fromJson(message, JsonObject.class);
            int op = msg.get("op").getAsInt();

            switch (op) {
                case 0: // Hello
                    handleHello(msg);
                    break;
                case 2: // Identified
                    authenticated = true;
                    System.out.println("[OBS Annotator] Successfully authenticated with OBS");
                    break;
                case 9: // Event (not used, but OBS sends them)
                    break;
                case 7: // RequestResponse
                    logRequestResponse(msg);
                    break;
                default:
                    break;
            }
        } catch (Exception e) {
            System.err.println("[OBS Annotator] Error processing message: " + e.getMessage());
        }
    }

    private void logRequestResponse(JsonObject msg) {
        try {
            JsonObject d = msg.getAsJsonObject("d");
            String requestType = d.has("requestType") ? d.get("requestType").getAsString() : "unknown";
            String requestId = d.has("requestId") ? d.get("requestId").getAsString() : "unknown";
            JsonObject status = d.getAsJsonObject("requestStatus");
            if (status != null && status.has("result") && !status.get("result").getAsBoolean()) {
                String code = status.has("code") ? status.get("code").getAsString() : "unknown";
                String comment = status.has("comment") ? status.get("comment").getAsString() : "unknown";
                System.err.println("[OBS Annotator] Request failed (" + requestType + ", " + requestId + "): " + code + " - " + comment);
            }
        } catch (Exception e) {
            System.err.println("[OBS Annotator] Error logging request response: " + e.getMessage());
        }
    }

    private void handleHello(JsonObject msg) {
        try {
            JsonObject d = msg.getAsJsonObject("d");

            // Build Identify message
            JsonObject identify = new JsonObject();
            identify.addProperty("op", 1); // Identify opcode

            JsonObject identifyData = new JsonObject();
            identifyData.addProperty("rpcVersion", 1);

            // Handle authentication if required
            if (d.has("authentication") && !config.obsPassword.isEmpty()) {
                JsonObject auth = d.getAsJsonObject("authentication");
                String challenge = auth.get("challenge").getAsString();
                String salt = auth.get("salt").getAsString();

                // Generate authentication string
                String secret = base64Sha256(config.obsPassword + salt);
                String authString = base64Sha256(secret + challenge);

                identifyData.addProperty("authentication", authString);
            }

            identify.add("d", identifyData);
            send(GSON.toJson(identify));
        } catch (Exception e) {
            System.err.println("[OBS Annotator] Authentication error: " + e.getMessage());
        }
    }

    private String base64Sha256(String input) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] hash = digest.digest(input.getBytes(StandardCharsets.UTF_8));
        return Base64.getEncoder().encodeToString(hash);
    }

    @Override
    public void onClose(int code, String reason, boolean remote) {
        authenticated = false;
        System.out.println("[OBS Annotator] Disconnected from OBS: " + reason);
        scheduleReconnect();
    }

    @Override
    public void onError(Exception ex) {
        System.err.println("[OBS Annotator] WebSocket error: " + ex.getMessage());
        scheduleReconnect();
    }

    private void scheduleReconnect() {
        // Don't schedule if already scheduled or if closed intentionally
        if (reconnectTask != null && !reconnectTask.isDone()) {
            return;
        }

        // Calculate delay with exponential backoff
        int delay = Math.min(
            INITIAL_RECONNECT_DELAY_MS * (int) Math.pow(2, reconnectAttempts),
            MAX_RECONNECT_DELAY_MS
        );

        reconnectAttempts++;
        System.out.println("[OBS Annotator] Reconnecting in " + (delay / 1000) + " seconds (attempt " + reconnectAttempts + ")");

        reconnectTask = scheduler.schedule(() -> {
            try {
                if (reconnectCallback != null) {
                    reconnectCallback.onReconnect();
                }
            } catch (Exception e) {
                System.err.println("[OBS Annotator] Reconnection failed: " + e.getMessage());
            }
        }, delay, TimeUnit.MILLISECONDS);
    }

    public void cancelReconnect() {
        if (reconnectTask != null && !reconnectTask.isDone()) {
            reconnectTask.cancel(false);
            reconnectTask = null;
        }
    }

    public void sendAnnotation(String annotationText) {
        if (!authenticated || !isOpen()) {
            return;
        }

        try {
            JsonObject request = new JsonObject();
            request.addProperty("op", 6); // Request opcode

            JsonObject requestData = new JsonObject();
            requestData.addProperty("requestType", "CallVendorRequest");
            requestData.addProperty("requestId", UUID.randomUUID().toString());

            JsonObject requestDataInner = new JsonObject();
            requestDataInner.addProperty("vendorName", "streamup-chapter-manager");
            requestDataInner.addProperty("requestType", "setChapterMarker");

            JsonObject vendorRequest = new JsonObject();
            vendorRequest.addProperty("chapterName", annotationText);
            vendorRequest.addProperty("chapterSource", "Minecraft");

            requestDataInner.add("requestData", vendorRequest);
            requestData.add("requestData", requestDataInner);
            request.add("d", requestData);

            send(GSON.toJson(request));
        } catch (Exception e) {
            System.err.println("[OBS Annotator] Failed to send annotation: " + e.getMessage());
        }
    }

    public boolean isAuthenticated() {
        return authenticated;
    }
}
