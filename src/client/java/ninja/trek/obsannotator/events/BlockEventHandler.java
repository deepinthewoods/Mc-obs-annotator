package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import ninja.trek.obsannotator.ObsAnnotatorClient;

public class BlockEventHandler {

    public static void register() {
        // Block broken - includes block name
        PlayerBlockBreakEvents.AFTER.register((world, player, pos, state, blockEntity) -> {
            if (ObsAnnotatorClient.CONFIG.enableBlockEvents &&
                ObsAnnotatorClient.CONFIG.blockBroken) {

                Block block = state.getBlock();
                if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerBlockBreak(block)) {
                    String blockName = block.getName().getString();
                    ObsAnnotatorClient.sendAnnotation("Block Break - " + blockName);
                }
            }
        });

        // Block placed (player holding a block item) - main hand only to prevent duplicates
        UseBlockCallback.EVENT.register((player, world, hand, hitResult) -> {
            if (ObsAnnotatorClient.CONFIG.enableBlockEvents &&
                ObsAnnotatorClient.CONFIG.blockPlaced &&
                hand == InteractionHand.MAIN_HAND) {

                ItemStack stack = player.getItemInHand(hand);
                if (stack.getItem() instanceof BlockItem blockItem &&
                    ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Block Place")) {
                    String blockName = blockItem.getBlock().getName().getString();
                    ObsAnnotatorClient.sendAnnotation("Block Place - " + blockName);
                }
            }
            return InteractionResult.PASS;
        });

        // Reset block break tracking each tick
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            ObsAnnotatorClient.EVENT_TRACKER.resetBlockBreakTracking();
        });
    }
}
