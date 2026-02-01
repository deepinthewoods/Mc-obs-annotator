package ninja.trek.obsannotator;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientLifecycleEvents;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
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
	private static KeyMapping keyPoiA;
	private static KeyMapping keyPoiB;
	private static KeyMapping keyNewSection;

	// Auto recording state tracking
	private boolean wasInWorld = false;
	private boolean wasWindowFocused = false;
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
		keyStart = KeyBindingHelper.registerKeyBinding(new KeyMapping(
			"key.obsannotator.start",
			GLFW.GLFW_KEY_KP_7,
			KEYBIND_CATEGORY
		));

		keyEnd = KeyBindingHelper.registerKeyBinding(new KeyMapping(
			"key.obsannotator.end",
			GLFW.GLFW_KEY_KP_9,
			KEYBIND_CATEGORY
		));

		keyPoiA = KeyBindingHelper.registerKeyBinding(new KeyMapping(
			"key.obsannotator.poi_a",
			GLFW.GLFW_KEY_KP_4,
			KEYBIND_CATEGORY
		));

		keyPoiB = KeyBindingHelper.registerKeyBinding(new KeyMapping(
			"key.obsannotator.poi_b",
			GLFW.GLFW_KEY_KP_6,
			KEYBIND_CATEGORY
		));

		keyNewSection = KeyBindingHelper.registerKeyBinding(new KeyMapping(
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
			while (keyPoiA.consumeClick()) {
				sendAnnotation("POI A");
			}
			while (keyPoiB.consumeClick()) {
				sendAnnotation("POI B");
			}
			while (keyNewSection.consumeClick()) {
				if (CONFIG.enableSectionMarker) {
					sendAnnotation("New Section");
				}
			}

			// Auto recording logic
			if (CONFIG.enableAutoRecording) {
				updateAutoRecording(client);
			}
		});
	}

	private void updateAutoRecording(net.minecraft.client.Minecraft client) {
		boolean inWorld = client.player != null && client.level != null;
		boolean windowFocused = client.isWindowActive();

		// Detect state changes
		boolean justJoinedWorld = inWorld && !wasInWorld;
		boolean justLeftWorld = !inWorld && wasInWorld;
		boolean justLostFocus = inWorld && !windowFocused && wasWindowFocused;
		boolean justGainedFocus = inWorld && windowFocused && !wasWindowFocused;

		// Handle state transitions
		if (justJoinedWorld && windowFocused) {
			// Player joined world with window focused - start recording
			startRecordingIfNotAlready();
		} else if (justLeftWorld) {
			// Player left world - stop recording
			stopRecordingIfActive();
		} else if (justLostFocus) {
			// Alt-tabbed out while in world - stop recording
			stopRecordingIfActive();
		} else if (justGainedFocus) {
			// Alt-tabbed back in while in world - start new recording
			startRecordingIfNotAlready();
		}

		// Update previous state
		wasInWorld = inWorld;
		wasWindowFocused = windowFocused;
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
