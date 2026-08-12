package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import ninja.trek.obsannotator.ObsAnnotatorClient;

public class CombatEventHandler {
    private static float lastHealth = -1;

    public static void register() {
        // Entity attacked - main hand only to prevent dual-hand duplicates
        AttackEntityCallback.EVENT.register((player, world, hand, entity, hitResult) -> {
            if (hand == InteractionHand.MAIN_HAND &&
                ObsAnnotatorClient.CONFIG.enableCombatEvents &&
                ObsAnnotatorClient.CONFIG.combatEntityAttacked &&
                ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Entity Attacked")) {
                String entityName = entity.getName().getString();
                ObsAnnotatorClient.sendAnnotation("Entity Attacked - " + entityName);
            }
            return InteractionResult.PASS;
        });

        // Check for health changes (death, damage, near-death) and new combat events
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
                ObsAnnotatorClient.EVENT_TRACKER.setPreviousTickHealth(currentHealth);
                return;
            }

            float previousTickHealth = ObsAnnotatorClient.EVENT_TRACKER.getPreviousTickHealth();

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

            // Totem pop detection: health was very low/0, now positive with absorption effect
            if (previousTickHealth <= 0 && currentHealth > 0 &&
                player.hasEffect(MobEffects.ABSORPTION) &&
                player.hasEffect(MobEffects.REGENERATION) &&
                player.hasEffect(MobEffects.FIRE_RESISTANCE)) {
                if (ObsAnnotatorClient.CONFIG.enableCombatEvents &&
                    ObsAnnotatorClient.CONFIG.combatTotemPop &&
                    ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Totem Pop")) {
                    ObsAnnotatorClient.sendAnnotation("Combat - Totem of Undying");
                }
            }

            // Damage taken (with source info)
            if (currentHealth < lastHealth && currentHealth > 0) {
                if (ObsAnnotatorClient.CONFIG.enableCombatEvents &&
                    ObsAnnotatorClient.CONFIG.combatDamageTaken) {
                    String damageText = "Combat - Damage Taken";
                    DamageSource lastDamageSource = player.getLastDamageSource();
                    if (lastDamageSource != null) {
                        Entity sourceEntity = lastDamageSource.getEntity();
                        if (sourceEntity != null) {
                            damageText = "Combat - Damage Taken (" + sourceEntity.getName().getString() + ")";
                        } else {
                            String damageType = lastDamageSource.type().msgId();
                            damageText = "Combat - Damage Taken (" + damageType + ")";
                        }
                    }
                    ObsAnnotatorClient.sendAnnotation(damageText);
                }
            }

            // Shield block detection: player is blocking and took a hit (hurtTime > 0)
            boolean isBlocking = player.isBlocking();
            if (isBlocking && player.hurtTime > 0 && !ObsAnnotatorClient.EVENT_TRACKER.wasShieldBlocking()) {
                if (ObsAnnotatorClient.CONFIG.enableCombatEvents &&
                    ObsAnnotatorClient.CONFIG.combatShieldBlock &&
                    ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Shield Block")) {
                    ObsAnnotatorClient.sendAnnotation("Combat - Shield Block");
                }
            }
            ObsAnnotatorClient.EVENT_TRACKER.setWasShieldBlocking(isBlocking && player.hurtTime > 0);

            // Near-death check (below 2 hearts = 4 health points)
            boolean isNearDeath = currentHealth < 4.0f && currentHealth > 0;
            if (ObsAnnotatorClient.CONFIG.enableCombatEvents &&
                ObsAnnotatorClient.CONFIG.combatNearDeath &&
                ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerNearDeath(isNearDeath)) {
                ObsAnnotatorClient.sendAnnotation("Combat - Near Death");
            }

            // Lava contact
            boolean inLava = player.isInLava();
            if (inLava && !ObsAnnotatorClient.EVENT_TRACKER.wasInLava()) {
                if (ObsAnnotatorClient.CONFIG.enableCombatEvents &&
                    ObsAnnotatorClient.CONFIG.combatLavaContact &&
                    ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Lava Contact")) {
                    ObsAnnotatorClient.sendAnnotation("Damage - Lava Contact");
                }
            }
            ObsAnnotatorClient.EVENT_TRACKER.setWasInLava(inLava);

            // Set on fire (excluding lava to avoid double-trigger)
            boolean onFire = player.isOnFire();
            if (onFire && !ObsAnnotatorClient.EVENT_TRACKER.wasOnFire() && !inLava) {
                if (ObsAnnotatorClient.CONFIG.enableCombatEvents &&
                    ObsAnnotatorClient.CONFIG.combatOnFire &&
                    ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("On Fire")) {
                    ObsAnnotatorClient.sendAnnotation("Damage - On Fire");
                }
            }
            ObsAnnotatorClient.EVENT_TRACKER.setWasOnFire(onFire);

            // Drowning
            boolean drowning = player.getAirSupply() <= 0;
            if (drowning && !ObsAnnotatorClient.EVENT_TRACKER.wasDrowning()) {
                if (ObsAnnotatorClient.CONFIG.enableCombatEvents &&
                    ObsAnnotatorClient.CONFIG.combatDrowning &&
                    ObsAnnotatorClient.EVENT_TRACKER.shouldTriggerAnnotation("Drowning")) {
                    ObsAnnotatorClient.sendAnnotation("Damage - Drowning");
                }
            }
            ObsAnnotatorClient.EVENT_TRACKER.setWasDrowning(drowning);

            ObsAnnotatorClient.EVENT_TRACKER.setPreviousTickHealth(currentHealth);
            lastHealth = currentHealth;
        });
    }
}
