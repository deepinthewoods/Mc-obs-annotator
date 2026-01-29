package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.player.LocalPlayer;
import ninja.trek.obsannotator.ObsAnnotatorClient;

public class FallEventHandler {

    public static void register() {
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            LocalPlayer player = client.player;
            if (player == null ||
                !ObsAnnotatorClient.CONFIG.enableFallEvents ||
                !ObsAnnotatorClient.CONFIG.fallLanded) {
                return;
            }

            boolean onGround = player.onGround();
            boolean falling = !onGround && player.getDeltaMovement().y < 0;

            if (falling) {
                // Player is in the air and moving downward - start tracking fall
                long currentTick = player.level().getGameTime();
                ObsAnnotatorClient.EVENT_TRACKER.startFalling(currentTick);
            } else if (onGround && ObsAnnotatorClient.EVENT_TRACKER.wasFalling()) {
                // Player just landed
                long currentTick = player.level().getGameTime();
                long durationTicks = ObsAnnotatorClient.EVENT_TRACKER.landedFromFall(
                    currentTick, ObsAnnotatorClient.CONFIG.fallMinDurationMs);
                if (durationTicks > 0) {
                    double durationSeconds = (durationTicks * 50) / 1000.0;
                    String formatted = String.format("Fall Landed (%.1fs)", durationSeconds);
                    ObsAnnotatorClient.sendAnnotation(formatted);
                }
            } else if (!onGround && !falling) {
                // Player is going up (jumping) - cancel any fall tracking
                ObsAnnotatorClient.EVENT_TRACKER.cancelFall();
            }
        });
    }
}
