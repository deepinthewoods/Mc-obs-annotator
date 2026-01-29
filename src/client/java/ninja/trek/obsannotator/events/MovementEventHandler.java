package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.Entity;
import ninja.trek.obsannotator.ObsAnnotatorClient;

public class MovementEventHandler {

    public static void register() {
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            LocalPlayer player = client.player;
            if (player == null || !ObsAnnotatorClient.CONFIG.enableMovementEvents) {
                return;
            }

            trackElytra(player);
            trackMount(player);
        });
    }

    private static void trackElytra(LocalPlayer player) {
        boolean isElytraFlying = player.isFallFlying();
        boolean wasElytraFlying = ObsAnnotatorClient.EVENT_TRACKER.wasElytraFlying();

        if (isElytraFlying && !wasElytraFlying) {
            // Started elytra flight
            if (ObsAnnotatorClient.CONFIG.movementElytraStart &&
                ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Elytra Start")) {
                ObsAnnotatorClient.sendAnnotation("Elytra - Started Flying");
            }
        } else if (!isElytraFlying && wasElytraFlying && player.onGround()) {
            // Landed from elytra flight
            if (ObsAnnotatorClient.CONFIG.movementElytraLand &&
                ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Elytra Land")) {
                ObsAnnotatorClient.sendAnnotation("Elytra - Landed");
            }
        }

        ObsAnnotatorClient.EVENT_TRACKER.setWasElytraFlying(isElytraFlying);
    }

    private static void trackMount(LocalPlayer player) {
        Entity currentVehicle = player.getVehicle();
        Entity lastVehicle = ObsAnnotatorClient.EVENT_TRACKER.getLastVehicle();

        if (currentVehicle != null && lastVehicle == null) {
            // Mounted
            if (ObsAnnotatorClient.CONFIG.movementMountRide &&
                ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Mount Ride")) {
                String entityName = currentVehicle.getName().getString();
                ObsAnnotatorClient.sendAnnotation("Mount - Riding " + entityName);
            }
        } else if (currentVehicle == null && lastVehicle != null) {
            // Dismounted
            if (ObsAnnotatorClient.CONFIG.movementMountDismount &&
                ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Mount Dismount")) {
                ObsAnnotatorClient.sendAnnotation("Mount - Dismounted");
            }
        }

        ObsAnnotatorClient.EVENT_TRACKER.setLastVehicle(currentVehicle);
    }
}
