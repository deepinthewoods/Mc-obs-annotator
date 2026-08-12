package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientEntityEvents;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.boss.enderdragon.EnderDragon;
import net.minecraft.world.entity.boss.wither.WitherBoss;
import ninja.trek.obsannotator.ObsAnnotatorClient;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

public class BossEventHandler {
    private static final Set<UUID> trackedDragons = new HashSet<>();
    private static final Set<UUID> trackedWithers = new HashSet<>();

    public static void register() {
        // Track entity loading for boss spawns
        ClientEntityEvents.ENTITY_LOAD.register((entity, world) -> {
            if (!ObsAnnotatorClient.CONFIG.enableBossEvents) {
                return;
            }

            if (entity instanceof EnderDragon dragon) {
                if (trackedDragons.add(dragon.getUUID()) &&
                    ObsAnnotatorClient.CONFIG.bossEnderDragonSpawned) {
                    ObsAnnotatorClient.sendAnnotation("Boss - Ender Dragon Spawned");
                }
            } else if (entity instanceof WitherBoss wither) {
                if (trackedWithers.add(wither.getUUID()) &&
                    ObsAnnotatorClient.CONFIG.bossWitherSpawned) {
                    ObsAnnotatorClient.sendAnnotation("Boss - Wither Spawned");
                }
            }
        });

        // Track entity unloading for cleanup and death detection
        ClientEntityEvents.ENTITY_UNLOAD.register((entity, world) -> {
            if (!ObsAnnotatorClient.CONFIG.enableBossEvents) {
                return;
            }

            if (entity instanceof EnderDragon dragon) {
                // Check if dragon is dead
                if (dragon.isDeadOrDying() && ObsAnnotatorClient.CONFIG.bossEnderDragonDefeated) {
                    ObsAnnotatorClient.sendAnnotation("Boss - Ender Dragon Defeated");
                }
                trackedDragons.remove(dragon.getUUID());
            } else if (entity instanceof WitherBoss wither) {
                // Check if wither is dead
                if (wither.isDeadOrDying() && ObsAnnotatorClient.CONFIG.bossWitherDefeated) {
                    ObsAnnotatorClient.sendAnnotation("Boss - Wither Defeated");
                }
                trackedWithers.remove(wither.getUUID());
            }
        });
    }
}
