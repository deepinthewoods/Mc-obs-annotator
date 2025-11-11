package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.InteractionResult;
import ninja.trek.obsannotator.ObsAnnotatorClient;

public class CombatEventHandler {
    private static float lastHealth = -1;

    public static void register() {
        // Entity attacked
        AttackEntityCallback.EVENT.register((player, world, hand, entity, hitResult) -> {
            if (ObsAnnotatorClient.CONFIG.enableCombatEvents &&
                ObsAnnotatorClient.CONFIG.combatEntityAttacked) {
                ObsAnnotatorClient.sendAnnotation("Combat - Entity Attacked");
            }
            return InteractionResult.PASS;
        });

        // Check for health changes (death, damage, near-death)
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            LocalPlayer player = client.player;
            if (player == null) {
                lastHealth = -1;
                return;
            }

            float currentHealth = player.getHealth();

            // First tick initialization
            if (lastHealth == -1) {
                lastHealth = currentHealth;
                return;
            }

            // Player death (health went to 0 or below)
            if (currentHealth <= 0 && lastHealth > 0) {
                if (ObsAnnotatorClient.CONFIG.enableCombatEvents &&
                    ObsAnnotatorClient.CONFIG.combatPlayerDeath) {
                    ObsAnnotatorClient.sendAnnotation("Combat - Player Death");
                }
                ObsAnnotatorClient.EVENT_TRACKER.reset();
            }

            // Player respawn (health restored from 0)
            if (currentHealth > 0 && lastHealth <= 0) {
                if (ObsAnnotatorClient.CONFIG.enableCombatEvents &&
                    ObsAnnotatorClient.CONFIG.combatPlayerRespawn) {
                    ObsAnnotatorClient.sendAnnotation("Combat - Player Respawn");
                }
            }

            // Damage taken
            if (currentHealth < lastHealth && currentHealth > 0) {
                if (ObsAnnotatorClient.CONFIG.enableCombatEvents &&
                    ObsAnnotatorClient.CONFIG.combatDamageTaken) {
                    ObsAnnotatorClient.sendAnnotation("Combat - Damage Taken");
                }

                // Check for fall damage (4+ hearts)
                float damageTaken = lastHealth - currentHealth;
                if (damageTaken >= 4.0f &&
                    ObsAnnotatorClient.CONFIG.enableFallDamageEvents &&
                    ObsAnnotatorClient.CONFIG.fallHighDamage) {
                    // Note: This triggers on ANY damage >= 4, not just fall damage
                    // A more precise check would require damage source tracking
                    ObsAnnotatorClient.sendAnnotation("Fall - High Damage");
                }
            }

            // Near-death check (below 2 hearts = 4 health points)
            boolean isNearDeath = currentHealth < 4.0f && currentHealth > 0;
            if (ObsAnnotatorClient.CONFIG.enableCombatEvents &&
                ObsAnnotatorClient.CONFIG.combatNearDeath &&
                ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerNearDeath(isNearDeath)) {
                ObsAnnotatorClient.sendAnnotation("Combat - Near Death");
            }

            lastHealth = currentHealth;
        });
    }
}
