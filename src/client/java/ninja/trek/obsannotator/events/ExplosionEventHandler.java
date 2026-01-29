package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.item.PrimedTnt;
import net.minecraft.world.phys.AABB;
import ninja.trek.obsannotator.ObsAnnotatorClient;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/**
 * Handles explosion detection.
 * Detects TNT ignition by tracking new PrimedTnt entities near the player.
 */
public class ExplosionEventHandler {
    private static final Set<UUID> trackedTntUUIDs = new HashSet<>();

    public static void register() {
        ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> {
            trackedTntUUIDs.clear();
        });

        // TNT ignited detection - scan for new PrimedTnt entities near player
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            LocalPlayer player = client.player;
            if (player == null || !ObsAnnotatorClient.CONFIG.enableExplosionEvents) {
                return;
            }

            if (ObsAnnotatorClient.CONFIG.explosionTntIgnited) {
                trackTntIgnited(player);
            }
        });
    }

    private static void trackTntIgnited(LocalPlayer player) {
        AABB searchBox = player.getBoundingBox().inflate(16.0);
        List<PrimedTnt> tntEntities = player.level().getEntitiesOfClass(PrimedTnt.class, searchBox);

        for (PrimedTnt tnt : tntEntities) {
            if (trackedTntUUIDs.add(tnt.getUUID())) {
                if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("TNT Ignited")) {
                    ObsAnnotatorClient.sendAnnotation("Explosion - TNT Ignited");
                }
                break; // One per tick
            }
        }

        // Clean up old UUIDs if the set grows too large
        if (trackedTntUUIDs.size() > 100) {
            trackedTntUUIDs.clear();
        }
    }

    /**
     * This method should be called from a mixin that intercepts explosion events.
     */
    public static void onExplosion(double x, double y, double z) {
        if (!ObsAnnotatorClient.CONFIG.enableExplosionEvents) {
            return;
        }

        if (ObsAnnotatorClient.CONFIG.explosionOther &&
            ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Explosion - Other")) {
            ObsAnnotatorClient.sendAnnotation("Explosion - Other");
        }
    }
}
