package ninja.trek.obsannotator;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientLifecycleEvents;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.minecraft.client.KeyMapping;
import net.minecraft.resources.Identifier;
import ninja.trek.obsannotator.config.ObsAnnotatorConfig;
import ninja.trek.obsannotator.events.*;
import ninja.trek.obsannotator.websocket.ObsWebSocketClient;
import org.lwjgl.glfw.GLFW;

public class ObsAnnotatorClient implements ClientModInitializer {
	public static ObsAnnotatorConfig CONFIG;
	public static ObsWebSocketClient WS_CLIENT;
	public static EventTracker EVENT_TRACKER;

	// Custom keybinding category
	private static final KeyMapping.Category KEYBIND_CATEGORY =
		KeyMapping.Category.register(Identifier.fromNamespaceAndPath("obsannotator", "general"));

	// Keybindings
	private static KeyMapping keyStart;
	private static KeyMapping keyEnd;
	private static KeyMapping keyPoi1m;
	private static KeyMapping keyPoi3m;
	private static KeyMapping keyPoi5m;
	private static KeyMapping keyNewSection;

	// Auto recording state tracking
	private boolean isRecording = false;

	@Override
	public void onInitializeClient() {
		// Load configuration
		CONFIG = ObsAnnotatorConfig.load();
		EVENT_TRACKER = new EventTracker();

		// Initialize WebSocket client
		initWebSocket();

		// Register keybindings
		registerKeybindings();

		// Register event handlers
		CombatEventHandler.register();
		BossEventHandler.register();
		BlockEventHandler.register();
		ItemEventHandler.register();
		ExplorationEventHandler.register();
		AchievementEventHandler.register();
		ExplosionEventHandler.register();
		FallEventHandler.register();
		InteractionEventHandler.register();
		MovementEventHandler.register();
		EnvironmentEventHandler.register();
		StatusEffectEventHandler.register();

		// Test mode support
		if (TestModeHandler.isTestMode()) {
			TestModeHandler.register();
			System.out.println("[OBS Annotator] TEST MODE ACTIVE");
		}

		if (CraneshotIntegration.isFollower()) {
			System.out.println(
				"[OBS Annotator] Detected " + CraneshotIntegration.getFollowerInstanceName() +
				"; annotations remain enabled and OBS recording control is disabled"
			);
		}

		// Register shutdown handler to stop recording when game closes
		ClientLifecycleEvents.CLIENT_STOPPING.register(client -> {
			System.out.println("[OBS Annotator] Game closing, stopping recording if active");
			stopRecordingIfActive();
			if (WS_CLIENT != null) {
				try {
					WS_CLIENT.closeBlocking();
				} catch (Exception e) {
					System.err.println("[OBS Annotator] Error closing WebSocket: " + e.getMessage());
				}
			}
		});

		System.out.println("[OBS Annotator] Initialized successfully");
	}

	private void initWebSocket() {
		try {
			WS_CLIENT = new ObsWebSocketClient(CONFIG);
			WS_CLIENT.setReconnectCallback(this::handleReconnect);
			// Connect asynchronously to avoid blocking Minecraft startup
			new Thread(() -> {
				try {
					WS_CLIENT.connect();
				} catch (Exception e) {
					System.err.println("[OBS Annotator] Failed to connect to OBS: " + e.getMessage());
				}
			}, "OBS-Annotator-Connection").start();
		} catch (Exception e) {
			System.err.println("[OBS Annotator] Failed to initialize WebSocket: " + e.getMessage());
		}
	}

	private void handleReconnect() {
		try {
			// Check if config file has been modified and reload if necessary
			if (ObsAnnotatorConfig.hasConfigFileChanged()) {
				System.out.println("[OBS Annotator] Config file changed, reloading settings from " +
					ObsAnnotatorConfig.getConfigPath());
				CONFIG = ObsAnnotatorConfig.load();
			}

			// Close existing client if still open
			if (WS_CLIENT != null) {
				WS_CLIENT.cancelReconnect();
				if (WS_CLIENT.isOpen()) {
					WS_CLIENT.close();
				}
			}

			// Create new client with potentially updated config
			WS_CLIENT = new ObsWebSocketClient(CONFIG);
			WS_CLIENT.setReconnectCallback(this::handleReconnect);
			// Connect asynchronously to avoid blocking
			new Thread(() -> {
				try {
					WS_CLIENT.connect();
				} catch (Exception e) {
					System.err.println("[OBS Annotator] Failed to reconnect to OBS: " + e.getMessage());
				}
			}, "OBS-Annotator-Reconnection").start();
		} catch (Exception e) {
			System.err.println("[OBS Annotator] Failed to reconnect WebSocket: " + e.getMessage());
		}
	}

	private void registerKeybindings() {
		keyStart = KeyMappingHelper.registerKeyMapping(new KeyMapping(
			"key.obsannotator.start",
			GLFW.GLFW_KEY_KP_1,
			KEYBIND_CATEGORY
		));

		keyEnd = KeyMappingHelper.registerKeyMapping(new KeyMapping(
			"key.obsannotator.end",
			GLFW.GLFW_KEY_KP_3,
			KEYBIND_CATEGORY
		));

		keyPoi1m = KeyMappingHelper.registerKeyMapping(new KeyMapping(
			"key.obsannotator.poi_1m",
			GLFW.GLFW_KEY_KP_7,
			KEYBIND_CATEGORY
		));

		keyPoi3m = KeyMappingHelper.registerKeyMapping(new KeyMapping(
			"key.obsannotator.poi_3m",
			GLFW.GLFW_KEY_KP_8,
			KEYBIND_CATEGORY
		));

		keyPoi5m = KeyMappingHelper.registerKeyMapping(new KeyMapping(
			"key.obsannotator.poi_5m",
			GLFW.GLFW_KEY_KP_9,
			KEYBIND_CATEGORY
		));

		keyNewSection = KeyMappingHelper.registerKeyMapping(new KeyMapping(
			"key.obsannotator.new_section",
			GLFW.GLFW_KEY_KP_2,
			KEYBIND_CATEGORY
		));

		// Register tick event to check for key presses and auto recording
		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			while (keyStart.consumeClick()) {
				sendAnnotation("Start");
			}
			while (keyEnd.consumeClick()) {
				sendAnnotation("End");
			}
			while (keyPoi1m.consumeClick()) {
				sendAnnotation("POI 1m");
			}
			while (keyPoi3m.consumeClick()) {
				sendAnnotation("POI 3m");
			}
			while (keyPoi5m.consumeClick()) {
				sendAnnotation("POI 5m");
			}
			while (keyNewSection.consumeClick()) {
				if (CONFIG.enableSectionMarker) {
					sendAnnotation("New Section");
				}
			}

			// Auto recording logic. This is always evaluated so disabling the
			// setting while active cleanly relinquishes recording control.
			updateAutoRecording(client);
		});
	}

	private void updateAutoRecording(net.minecraft.client.Minecraft client) {
		boolean inWorld = client.player != null && client.level != null;

		// A shared wide recording must survive focus changes between Minecraft
		// windows. Craneshot followers annotate but never control OBS recording,
		// even when they share the main instance's config file.
		boolean shouldRecord = CONFIG.enableAutoRecording &&
			!CraneshotIntegration.isFollower() && inWorld;

		if (shouldRecord && !isRecording) {
			startRecordingIfNotAlready();
		} else if (!shouldRecord && isRecording) {
			stopRecordingIfActive();
		}
	}

	private void startRecordingIfNotAlready() {
		if (!isRecording && WS_CLIENT != null && WS_CLIENT.isAuthenticated()) {
			WS_CLIENT.startRecording();
			isRecording = true;
			System.out.println("[OBS Annotator] Auto-started recording");
		}
	}

	private void stopRecordingIfActive() {
		if (isRecording && WS_CLIENT != null && WS_CLIENT.isAuthenticated()) {
			WS_CLIENT.stopRecording();
			isRecording = false;
			System.out.println("[OBS Annotator] Auto-stopped recording");
		}
	}

	public static void sendAnnotation(String text) {
		if (WS_CLIENT != null && WS_CLIENT.isAuthenticated()) {
			WS_CLIENT.sendAnnotation(text);
		}
	}
}
