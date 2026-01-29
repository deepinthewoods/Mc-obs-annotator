package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.monster.warden.Warden;
import net.minecraft.world.entity.raid.Raider;
import net.minecraft.world.phys.AABB;
import ninja.trek.obsannotator.ObsAnnotatorClient;

import java.util.List;

public class EnvironmentEventHandler {
    private static int raiderCheckCooldown = 0;
    private static boolean raidersNearby = false;

    public static void register() {
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            LocalPlayer player = client.player;
            if (player == null || !ObsAnnotatorClient.CONFIG.enableEnvironmentEvents) {
                return;
            }

            trackLightning(player);
            trackWarden(player);
            trackRaid(player);
        });
    }

    private static void trackLightning(LocalPlayer player) {
        if (!ObsAnnotatorClient.CONFIG.environmentLightning) {
            return;
        }

        AABB searchBox = player.getBoundingBox().inflate(128.0);
        List<LightningBolt> bolts = player.level().getEntitiesOfClass(LightningBolt.class, searchBox);

        for (LightningBolt bolt : bolts) {
            if (ObsAnnotatorClient.EVENT_TRACKER.isNewLightning(bolt.getUUID())) {
                if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Lightning")) {
                    ObsAnnotatorClient.sendAnnotation("Environment - Lightning Strike");
                }
                break; // Only one annotation per tick
            }
        }
    }

    private static void trackWarden(LocalPlayer player) {
        if (!ObsAnnotatorClient.CONFIG.environmentWardenSummoned) {
            return;
        }

        AABB searchBox = player.getBoundingBox().inflate(64.0);
        List<Warden> wardens = player.level().getEntitiesOfClass(Warden.class, searchBox);

        for (Warden warden : wardens) {
            if (ObsAnnotatorClient.EVENT_TRACKER.isNewWarden(warden.getUUID())) {
                if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Warden Summoned")) {
                    ObsAnnotatorClient.sendAnnotation("Environment - Warden Summoned");
                }
                break;
            }
        }
    }

    private static void trackRaid(LocalPlayer player) {
        if (!ObsAnnotatorClient.CONFIG.environmentRaid) {
            return;
        }

        // Throttle raid checks to every 20 ticks (1 second)
        raiderCheckCooldown--;
        if (raiderCheckCooldown > 0) {
            return;
        }
        raiderCheckCooldown = 20;

        AABB searchBox = player.getBoundingBox().inflate(96.0);
        List<Raider> raiders = player.level().getEntitiesOfClass(Raider.class, searchBox);
        boolean raidersNow = raiders.size() >= 3; // Multiple raiders nearby suggests a raid

        if (raidersNow && !raidersNearby) {
            if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Raid Started")) {
                ObsAnnotatorClient.sendAnnotation("Environment - Raid Started");
            }
        }

        raidersNearby = raidersNow;
    }
}
