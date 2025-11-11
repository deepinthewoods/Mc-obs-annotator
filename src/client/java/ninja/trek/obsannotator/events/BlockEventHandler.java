package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.event.player.AttackBlockCallback;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.level.block.Block;
import ninja.trek.obsannotator.ObsAnnotatorClient;

public class BlockEventHandler {

    public static void register() {
        // Block broken
        PlayerBlockBreakEvents.AFTER.register((world, player, pos, state, blockEntity) -> {
            if (world.isClientSide &&
                ObsAnnotatorClient.CONFIG.enableBlockEvents &&
                ObsAnnotatorClient.CONFIG.blockBroken) {

                Block block = state.getBlock();
                if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerBlockBreak(block)) {
                    ObsAnnotatorClient.sendAnnotation("Block - Broken");
                }
            }
        });

        // Block left-clicked (attacked)
        AttackBlockCallback.EVENT.register((player, world, hand, pos, direction) -> {
            if (world.isClientSide &&
                ObsAnnotatorClient.CONFIG.enableBlockEvents &&
                ObsAnnotatorClient.CONFIG.blockLeftClick) {
                ObsAnnotatorClient.sendAnnotation("Block - Left Click");
            }
            return InteractionResult.PASS;
        });

        // Block right-clicked (used)
        UseBlockCallback.EVENT.register((player, world, hand, hitResult) -> {
            if (world.isClientSide &&
                ObsAnnotatorClient.CONFIG.enableBlockEvents &&
                ObsAnnotatorClient.CONFIG.blockRightClick) {
                ObsAnnotatorClient.sendAnnotation("Block - Right Click");
            }
            return InteractionResult.PASS;
        });

        // Reset block break tracking each tick
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            ObsAnnotatorClient.EVENT_TRACKER.resetBlockBreakTracking();
        });
    }
}
