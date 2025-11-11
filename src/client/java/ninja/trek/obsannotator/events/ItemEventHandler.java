package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import ninja.trek.obsannotator.ObsAnnotatorClient;

import java.util.HashMap;
import java.util.Map;

public class ItemEventHandler {
    private static final Map<Item, Integer> lastItemCounts = new HashMap<>();

    public static void register() {
        // Item used
        UseItemCallback.EVENT.register((player, world, hand) -> {
            if (world.isClientSide &&
                ObsAnnotatorClient.CONFIG.enableItemEvents &&
                ObsAnnotatorClient.CONFIG.itemUsed) {
                ObsAnnotatorClient.sendAnnotation("Item - Used");
            }
            return InteractionResult.PASS;
        });

        // Check for rare items obtained
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            LocalPlayer player = client.player;
            if (player == null ||
                !ObsAnnotatorClient.CONFIG.enableItemEvents ||
                !ObsAnnotatorClient.CONFIG.itemRareObtained) {
                return;
            }

            // Check inventory for rare items
            for (ItemStack stack : player.getInventory().items) {
                if (stack.isEmpty()) {
                    continue;
                }

                Item item = stack.getItem();
                int currentCount = stack.getCount();
                int previousCount = lastItemCounts.getOrDefault(item, 0);

                if (currentCount > previousCount && isRareItem(item)) {
                    ObsAnnotatorClient.sendAnnotation("Item - Rare Obtained");
                    break; // Only send once per tick
                }
            }

            // Update tracked counts
            lastItemCounts.clear();
            for (ItemStack stack : player.getInventory().items) {
                if (!stack.isEmpty()) {
                    Item item = stack.getItem();
                    lastItemCounts.merge(item, stack.getCount(), Integer::sum);
                }
            }
        });
    }

    private static boolean isRareItem(Item item) {
        return item == Items.DIAMOND ||
               item == Items.NETHERITE_INGOT ||
               item == Items.NETHERITE_SCRAP ||
               item == Items.ANCIENT_DEBRIS ||
               item == Items.ENCHANTED_BOOK ||
               item == Items.DIAMOND_ORE ||
               item == Items.DEEPSLATE_DIAMOND_ORE;
    }
}
