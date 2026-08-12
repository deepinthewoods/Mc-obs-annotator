package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biome;
import ninja.trek.obsannotator.ObsAnnotatorClient;

public class ExplorationEventHandler {

    public static void register() {
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            LocalPlayer player = client.player;
            if (player == null || !ObsAnnotatorClient.CONFIG.enableExplorationEvents) {
                return;
            }

            Level level = player.level();
            BlockPos pos = player.blockPosition();

            // Get current biome
            Holder<Biome> biomeHolder = level.getBiome(pos);
            biomeHolder.unwrapKey().ifPresent(biomeKey -> {
                long currentTime = System.currentTimeMillis();

                // Check for new biome type (first time visiting)
                if (ObsAnnotatorClient.CONFIG.explorationNewBiome &&
                    ObsAnnotatorClient.EVENT_TRACKER.isNewBiome(biomeKey)) {
                    ObsAnnotatorClient.sendAnnotation("Exploration - New Biome Type");
                }

                // Check for biome change (with cooldown)
                if (ObsAnnotatorClient.CONFIG.explorationBiomeChanged &&
                    ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerBiomeChange(
                        biomeKey,
                        currentTime,
                        ObsAnnotatorClient.CONFIG.biomeChangeCooldown)) {
                    ObsAnnotatorClient.sendAnnotation("Exploration - Biome Changed");
                }
            });

            // Structure detection is more complex and would require checking structure tags
            // This is a simplified implementation that checks for common structures
            // A full implementation would need to query the structure manager
            if (ObsAnnotatorClient.CONFIG.explorationStructureEntered) {
                checkForStructures(player, level, pos);
            }
        });
    }

    private static void checkForStructures(LocalPlayer player, Level level, BlockPos pos) {
        // This is a simplified structure check
        // In a full implementation, you would query level.structureManager()
        // For now, we'll skip this as it requires more complex integration
        // with Minecraft's structure system
    }
}
