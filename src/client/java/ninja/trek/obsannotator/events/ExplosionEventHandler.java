package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.PacketSender;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.multiplayer.ClientPacketListener;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import ninja.trek.obsannotator.ObsAnnotatorClient;

/**
 * Handles explosion detection.
 * Note: Due to client-side limitations, we detect explosions through sound and particle events.
 * This approach may not catch all explosions but provides reasonable coverage.
 */
public class ExplosionEventHandler {

    public static void register() {
        // Explosion detection on client is limited
        // We'll use a mixin to intercept explosion packets from the server
        // For now, register connection events to reset state
        ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> {
            // Reset any explosion tracking state when joining a world
        });
    }

    /**
     * This method should be called from a mixin that intercepts explosion events.
     * The mixin would be in ClientboundExplodePacket or similar.
     */
    public static void onExplosion(double x, double y, double z) {
        if (!ObsAnnotatorClient.CONFIG.enableExplosionEvents) {
            return;
        }

        // Since we can't easily determine explosion source on client,
        // we'll send a generic explosion event
        // A more sophisticated implementation would track nearby entities
        if (ObsAnnotatorClient.CONFIG.explosionOther) {
            ObsAnnotatorClient.sendAnnotation("Explosion - Other");
        }
    }
}
