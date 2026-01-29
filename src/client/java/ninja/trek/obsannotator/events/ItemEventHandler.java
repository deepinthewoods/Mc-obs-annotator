package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.core.component.DataComponents;
import net.minecraft.world.item.*;
import ninja.trek.obsannotator.ObsAnnotatorClient;

import java.util.HashMap;
import java.util.Map;

public class ItemEventHandler {
    private static final Map<Item, Integer> lastItemCounts = new HashMap<>();

    public static void register() {
        // Item used - semantic events based on item type, main hand only
        UseItemCallback.EVENT.register((player, world, hand) -> {
            if (hand != InteractionHand.MAIN_HAND ||
                !ObsAnnotatorClient.CONFIG.enableItemEvents) {
                return InteractionResult.PASS;
            }

            ItemStack stack = player.getItemInHand(hand);
            Item item = stack.getItem();
            String itemName = stack.getHoverName().getString();

            // Food
            if (stack.get(DataComponents.FOOD) != null) {
                if (ObsAnnotatorClient.CONFIG.foodEaten &&
                    ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Food Eaten")) {
                    ObsAnnotatorClient.sendAnnotation("Food Eaten - " + itemName);
                }
                return InteractionResult.PASS;
            }

            // Potion
            if (item instanceof PotionItem) {
                if (ObsAnnotatorClient.CONFIG.potionDrunk &&
                    ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Potion Drunk")) {
                    ObsAnnotatorClient.sendAnnotation("Potion Drunk - " + itemName);
                }
                return InteractionResult.PASS;
            }

            // Bow
            if (item instanceof BowItem) {
                if (ObsAnnotatorClient.CONFIG.bowFired &&
                    ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Bow Fired")) {
                    ObsAnnotatorClient.sendAnnotation("Bow Fired");
                }
                return InteractionResult.PASS;
            }

            // Crossbow
            if (item instanceof CrossbowItem) {
                if (ObsAnnotatorClient.CONFIG.bowFired &&
                    ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Crossbow Fired")) {
                    ObsAnnotatorClient.sendAnnotation("Crossbow Fired");
                }
                return InteractionResult.PASS;
            }

            // Trident
            if (item instanceof TridentItem) {
                if (ObsAnnotatorClient.CONFIG.bowFired &&
                    ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Trident Thrown")) {
                    ObsAnnotatorClient.sendAnnotation("Trident Thrown");
                }
                return InteractionResult.PASS;
            }

            // Ender Pearl
            if (item == Items.ENDER_PEARL) {
                if (ObsAnnotatorClient.CONFIG.enderPearlThrown &&
                    ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Ender Pearl Thrown")) {
                    ObsAnnotatorClient.sendAnnotation("Ender Pearl Thrown");
                }
                return InteractionResult.PASS;
            }

            // Catch-all for other items
            if (ObsAnnotatorClient.CONFIG.itemUsed &&
                ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Item Used")) {
                ObsAnnotatorClient.sendAnnotation("Item Used - " + itemName);
            }
            return InteractionResult.PASS;
        });

        // Check for tool break and rare items obtained
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            LocalPlayer player = client.player;
            if (player == null || !ObsAnnotatorClient.CONFIG.enableItemEvents) {
                return;
            }

            // Tool break detection
            if (ObsAnnotatorClient.CONFIG.itemToolBroke) {
                trackToolBreak(player);
            }

            if (!ObsAnnotatorClient.CONFIG.itemRareObtained) {
                return;
            }

            // Check inventory for rare items
            for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
                ItemStack stack = player.getInventory().getItem(i);
                if (stack.isEmpty()) {
                    continue;
                }

                Item item = stack.getItem();
                int currentCount = stack.getCount();
                int previousCount = lastItemCounts.getOrDefault(item, 0);

                if (currentCount > previousCount && isRareItem(item)) {
                    String itemName = stack.getHoverName().getString();
                    ObsAnnotatorClient.sendAnnotation("Rare Item - " + itemName);
                    break; // Only send once per tick
                }
            }

            // Update tracked counts
            lastItemCounts.clear();
            for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
                ItemStack stack = player.getInventory().getItem(i);
                if (!stack.isEmpty()) {
                    Item item = stack.getItem();
                    lastItemCounts.merge(item, stack.getCount(), Integer::sum);
                }
            }
        });
    }

    private static void trackToolBreak(LocalPlayer player) {
        ItemStack currentHeld = player.getMainHandItem();
        ItemStack lastHeld = ObsAnnotatorClient.EVENT_TRACKER.getLastHeldItemStack();
        int lastDurability = ObsAnnotatorClient.EVENT_TRACKER.getLastHeldItemDurability();

        // If we had an item with low durability last tick, and now it's gone (empty or different item)
        if (!lastHeld.isEmpty() && lastHeld.isDamageableItem() && lastDurability <= 1) {
            boolean itemGone = currentHeld.isEmpty() || !ItemStack.isSameItem(currentHeld, lastHeld);
            if (itemGone) {
                String itemName = lastHeld.getHoverName().getString();
                if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Tool Broke")) {
                    ObsAnnotatorClient.sendAnnotation("Item - Tool Broke (" + itemName + ")");
                }
            }
        }

        // Update tracking state
        if (!currentHeld.isEmpty() && currentHeld.isDamageableItem()) {
            ObsAnnotatorClient.EVENT_TRACKER.setLastHeldItemStack(currentHeld);
            ObsAnnotatorClient.EVENT_TRACKER.setLastHeldItemDurability(
                currentHeld.getMaxDamage() - currentHeld.getDamageValue());
        } else {
            ObsAnnotatorClient.EVENT_TRACKER.setLastHeldItemStack(ItemStack.EMPTY);
            ObsAnnotatorClient.EVENT_TRACKER.setLastHeldItemDurability(0);
        }
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
