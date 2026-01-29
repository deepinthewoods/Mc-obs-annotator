package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.Holder;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import ninja.trek.obsannotator.ObsAnnotatorClient;

import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public class StatusEffectEventHandler {

    public static void register() {
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            LocalPlayer player = client.player;
            if (player == null ||
                !ObsAnnotatorClient.CONFIG.enableStatusEffectEvents ||
                !ObsAnnotatorClient.CONFIG.statusEffectApplied) {
                return;
            }

            Map<Holder<MobEffect>, MobEffectInstance> activeEffects = player.getActiveEffectsMap();
            Set<Holder<MobEffect>> currentEffects = new HashSet<>(activeEffects.keySet());
            Set<Holder<MobEffect>> previousEffects = ObsAnnotatorClient.EVENT_TRACKER.getLastActiveEffects();

            // Find newly applied effects
            for (Holder<MobEffect> effect : currentEffects) {
                if (!previousEffects.contains(effect)) {
                    String effectName = effect.value().getDisplayName().getString();
                    if (ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Status Effect - " + effectName)) {
                        ObsAnnotatorClient.sendAnnotation("Status Effect - " + effectName);
                    }
                }
            }

            ObsAnnotatorClient.EVENT_TRACKER.setLastActiveEffects(currentEffects);
        });
    }
}
