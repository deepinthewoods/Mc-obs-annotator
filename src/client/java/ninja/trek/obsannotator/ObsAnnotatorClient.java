package ninja.trek.obsannotator;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.minecraft.client.KeyMapping;
import ninja.trek.obsannotator.config.ObsAnnotatorConfig;
import ninja.trek.obsannotator.events.*;
import ninja.trek.obsannotator.websocket.ObsWebSocketClient;
import org.lwjgl.glfw.GLFW;

public class ObsAnnotatorClient implements ClientModInitializer {
	public static ObsAnnotatorConfig CONFIG;
	public static ObsWebSocketClient WS_CLIENT;
	public static EventTracker EVENT_TRACKER;

	// Keybindings
	private static KeyMapping keyStart;
	private static KeyMapping keyEnd;
	private static KeyMapping keyPoiA;
	private static KeyMapping keyPoiB;

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

		System.out.println("[OBS Annotator] Initialized successfully");
	}

	private void initWebSocket() {
		try {
			WS_CLIENT = new ObsWebSocketClient(CONFIG);
			WS_CLIENT.connect();
		} catch (Exception e) {
			System.err.println("[OBS Annotator] Failed to initialize WebSocket: " + e.getMessage());
		}
	}

	private void registerKeybindings() {
		keyStart = KeyBindingHelper.registerKeyBinding(new KeyMapping(
			"key.obsannotator.start",
			GLFW.GLFW_KEY_KP_7,
			"category.obsannotator"
		));

		keyEnd = KeyBindingHelper.registerKeyBinding(new KeyMapping(
			"key.obsannotator.end",
			GLFW.GLFW_KEY_KP_9,
			"category.obsannotator"
		));

		keyPoiA = KeyBindingHelper.registerKeyBinding(new KeyMapping(
			"key.obsannotator.poi_a",
			GLFW.GLFW_KEY_KP_4,
			"category.obsannotator"
		));

		keyPoiB = KeyBindingHelper.registerKeyBinding(new KeyMapping(
			"key.obsannotator.poi_b",
			GLFW.GLFW_KEY_KP_6,
			"category.obsannotator"
		));

		// Register tick event to check for key presses
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
		});
	}

	public static void sendAnnotation(String text) {
		if (WS_CLIENT != null && WS_CLIENT.isAuthenticated()) {
			WS_CLIENT.sendAnnotation(text);
		}
	}
}
