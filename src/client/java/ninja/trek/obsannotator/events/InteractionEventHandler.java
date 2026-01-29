package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.inventory.CraftingScreen;
import net.minecraft.client.gui.screens.inventory.EnchantmentScreen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.gui.screens.inventory.MerchantScreen;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.CraftingMenu;
import net.minecraft.world.inventory.EnchantmentMenu;
import net.minecraft.world.inventory.InventoryMenu;
import net.minecraft.world.inventory.MerchantMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import ninja.trek.obsannotator.ObsAnnotatorClient;

public class InteractionEventHandler {
    // Crafting tracking
    private static ItemStack lastCraftingResult = ItemStack.EMPTY;
    private static boolean wasInCraftingScreen = false;

    // Trading tracking
    private static ItemStack lastTradeResult = ItemStack.EMPTY;
    private static boolean wasInMerchantScreen = false;

    // Enchanting tracking
    private static boolean wasInEnchantmentScreen = false;
    private static ItemStack lastEnchantInput = ItemStack.EMPTY;

    // Beacon tracking
    private static boolean hadBeaconEffect = false;

    public static void register() {
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            LocalPlayer player = client.player;
            if (player == null) {
                return;
            }

            if (ObsAnnotatorClient.CONFIG.enableInteractionEvents) {
                trackCrafting(client);
                trackTrading(client);
                trackEnchanting(client);
                trackPortal(player);
                trackSleep(player);
                trackBeacon(player);
            }
        });
    }

    private static void trackCrafting(Minecraft client) {
        if (!ObsAnnotatorClient.CONFIG.interactionCrafting) {
            return;
        }

        boolean inCraftingScreen = client.screen instanceof CraftingScreen || client.screen instanceof InventoryScreen;

        if (inCraftingScreen) {
            AbstractContainerMenu menu = client.player.containerMenu;
            // Result slot is slot 0 in both CraftingMenu and InventoryMenu
            Slot resultSlot = menu.getSlot(0);
            ItemStack currentResult = resultSlot.getItem();

            if (wasInCraftingScreen) {
                // Was non-empty, now empty → item was taken (crafted)
                if (!lastCraftingResult.isEmpty() && currentResult.isEmpty()) {
                    String itemName = lastCraftingResult.getHoverName().getString();
                    if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Crafted")) {
                        ObsAnnotatorClient.sendAnnotation("Crafted - " + itemName);
                    }
                }
            }

            lastCraftingResult = currentResult.copy();
            wasInCraftingScreen = true;
        } else {
            wasInCraftingScreen = false;
            lastCraftingResult = ItemStack.EMPTY;
        }
    }

    private static void trackTrading(Minecraft client) {
        if (!ObsAnnotatorClient.CONFIG.interactionTrading) {
            return;
        }

        boolean inMerchantScreen = client.screen instanceof MerchantScreen;

        if (inMerchantScreen) {
            AbstractContainerMenu menu = client.player.containerMenu;
            if (menu instanceof MerchantMenu merchantMenu) {
                // Result slot is slot 2 in MerchantMenu
                Slot resultSlot = menu.getSlot(2);
                ItemStack currentResult = resultSlot.getItem();

                if (wasInMerchantScreen) {
                    if (!lastTradeResult.isEmpty() && currentResult.isEmpty()) {
                        if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Trade Completed")) {
                            ObsAnnotatorClient.sendAnnotation("Trade Completed");
                        }
                    }
                }

                lastTradeResult = currentResult.copy();
            }
            wasInMerchantScreen = true;
        } else {
            wasInMerchantScreen = false;
            lastTradeResult = ItemStack.EMPTY;
        }
    }

    private static void trackEnchanting(Minecraft client) {
        if (!ObsAnnotatorClient.CONFIG.interactionEnchanting) {
            return;
        }

        boolean inEnchantmentScreen = client.screen instanceof EnchantmentScreen;

        if (inEnchantmentScreen) {
            AbstractContainerMenu menu = client.player.containerMenu;
            if (menu instanceof EnchantmentMenu enchantMenu) {
                // Slot 0 is the item input slot in EnchantmentMenu
                Slot inputSlot = menu.getSlot(0);
                ItemStack currentInput = inputSlot.getItem();

                if (wasInEnchantmentScreen) {
                    // If the item changed (enchantment was applied, item gets enchantment glint or changes)
                    if (!lastEnchantInput.isEmpty() && !currentInput.isEmpty() &&
                        currentInput.isEnchanted() && !lastEnchantInput.isEnchanted()) {
                        String itemName = currentInput.getHoverName().getString();
                        if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Enchanted")) {
                            ObsAnnotatorClient.sendAnnotation("Enchanted - " + itemName);
                        }
                    }
                }

                lastEnchantInput = currentInput.copy();
            }
            wasInEnchantmentScreen = true;
        } else {
            wasInEnchantmentScreen = false;
            lastEnchantInput = ItemStack.EMPTY;
        }
    }

    private static void trackPortal(LocalPlayer player) {
        if (!ObsAnnotatorClient.CONFIG.interactionPortal) {
            return;
        }

        ResourceKey<Level> currentDimension = player.level().dimension();
        ResourceKey<?> lastDimension = ObsAnnotatorClient.EVENT_TRACKER.getLastDimension();

        if (lastDimension != null && !currentDimension.equals(lastDimension)) {
            String annotation;
            if (currentDimension == Level.NETHER) {
                annotation = "Entered Nether";
            } else if (currentDimension == Level.END) {
                annotation = "Entered End";
            } else if (currentDimension == Level.OVERWORLD) {
                annotation = "Returned to Overworld";
            } else {
                annotation = "Dimension Changed";
            }

            if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Portal")) {
                ObsAnnotatorClient.sendAnnotation(annotation);
            }
        }

        ObsAnnotatorClient.EVENT_TRACKER.setLastDimension(currentDimension);
    }

    private static void trackBeacon(LocalPlayer player) {
        if (!ObsAnnotatorClient.CONFIG.interactionBeacon) {
            return;
        }

        // Detect beacon activation by checking for beacon-specific effects
        // Beacons give effects like HASTE, SPEED, RESISTANCE, JUMP_BOOST, STRENGTH, REGENERATION
        // Conduit gives CONDUIT_POWER
        boolean hasBeaconEffect = player.hasEffect(MobEffects.CONDUIT_POWER);
        // Also check for common beacon effects — but these could come from potions too.
        // Conduit Power is unique to conduits, so it's the safest signal.

        if (hasBeaconEffect && !hadBeaconEffect) {
            if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Beacon Activated")) {
                ObsAnnotatorClient.sendAnnotation("Interaction - Beacon Activated");
            }
        }

        hadBeaconEffect = hasBeaconEffect;
    }

    private static void trackSleep(LocalPlayer player) {
        if (!ObsAnnotatorClient.CONFIG.interactionSleep) {
            return;
        }

        boolean isSleeping = player.isSleeping();
        boolean wasSleeping = ObsAnnotatorClient.EVENT_TRACKER.wasSleeping();

        if (isSleeping && !wasSleeping) {
            if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Sleep")) {
                ObsAnnotatorClient.sendAnnotation("Started Sleeping");
            }
        } else if (!isSleeping && wasSleeping) {
            if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Wake")) {
                ObsAnnotatorClient.sendAnnotation("Woke Up");
            }
        }

        ObsAnnotatorClient.EVENT_TRACKER.setWasSleeping(isSleeping);
    }
}
