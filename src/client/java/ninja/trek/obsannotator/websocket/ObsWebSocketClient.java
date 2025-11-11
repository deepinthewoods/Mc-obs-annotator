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

public class ObsWebSocketClient extends WebSocketClient {
    private static final Gson GSON = new Gson();
    private final ObsAnnotatorConfig config;
    private boolean authenticated = false;

    public ObsWebSocketClient(ObsAnnotatorConfig config) throws Exception {
        super(new URI("ws://" + config.obsHost + ":" + config.obsPort));
        this.config = config;
        this.setConnectionLostTimeout(10);
    }

    @Override
    public void onOpen(ServerHandshake handshake) {
        System.out.println("[OBS Annotator] Connected to OBS WebSocket");
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
                default:
                    break;
            }
        } catch (Exception e) {
            System.err.println("[OBS Annotator] Error processing message: " + e.getMessage());
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
    }

    @Override
    public void onError(Exception ex) {
        System.err.println("[OBS Annotator] WebSocket error: " + ex.getMessage());
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
            requestDataInner.addProperty("requestType", "setAnnotation");

            JsonObject vendorRequest = new JsonObject();
            vendorRequest.addProperty("annotationText", annotationText);
            vendorRequest.addProperty("annotationSource", "Minecraft");

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
