package ninja.trek.obsannotator.config;

import me.shedaniel.clothconfig2.api.ConfigBuilder;
import me.shedaniel.clothconfig2.api.ConfigCategory;
import me.shedaniel.clothconfig2.api.ConfigEntryBuilder;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import ninja.trek.obsannotator.ObsAnnotatorClient;

public class ObsAnnotatorConfigScreen {

    public static Screen create(Screen parent) {
        ObsAnnotatorConfig config = ObsAnnotatorClient.CONFIG;
        ObsAnnotatorConfig defaults = new ObsAnnotatorConfig();

        ConfigBuilder builder = ConfigBuilder.create()
                .setParentScreen(parent)
                .setTitle(Component.translatable("config.obsannotator.title"))
                .setSavingRunnable(config::save);

        ConfigEntryBuilder entry = builder.entryBuilder();

        // --- General ---
        ConfigCategory general = builder.getOrCreateCategory(Component.translatable("config.obsannotator.category.general"));

        general.addEntry(entry.startStrField(Component.translatable("config.obsannotator.obsHost"), config.obsHost)
                .setDefaultValue(defaults.obsHost)
                .setSaveConsumer(val -> config.obsHost = val)
                .build());

        general.addEntry(entry.startIntField(Component.translatable("config.obsannotator.obsPort"), config.obsPort)
                .setDefaultValue(defaults.obsPort)
                .setSaveConsumer(val -> config.obsPort = val)
                .build());

        general.addEntry(entry.startStrField(Component.translatable("config.obsannotator.obsPassword"), config.obsPassword)
                .setDefaultValue(defaults.obsPassword)
                .setSaveConsumer(val -> config.obsPassword = val)
                .build());

        general.addEntry(entry.startStrField(Component.translatable("config.obsannotator.instanceName"), config.instanceName)
                .setDefaultValue(defaults.instanceName)
                .setSaveConsumer(val -> config.instanceName = val)
                .setTooltip(Component.translatable("config.obsannotator.instanceName.tooltip"))
                .build());

        general.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enableAutoRecording"), config.enableAutoRecording)
                .setDefaultValue(defaults.enableAutoRecording)
                .setSaveConsumer(val -> config.enableAutoRecording = val)
                .setTooltip(Component.translatable("config.obsannotator.enableAutoRecording.tooltip"))
                .build());

        general.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enableSectionMarker"), config.enableSectionMarker)
                .setDefaultValue(defaults.enableSectionMarker)
                .setSaveConsumer(val -> config.enableSectionMarker = val)
                .build());

        // --- Combat Events ---
        ConfigCategory combat = builder.getOrCreateCategory(Component.translatable("config.obsannotator.category.combat"));

        combat.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enableCombatEvents"), config.enableCombatEvents)
                .setDefaultValue(defaults.enableCombatEvents)
                .setSaveConsumer(val -> config.enableCombatEvents = val)
                .build());

        combat.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.combatEntityAttacked"), config.combatEntityAttacked)
                .setDefaultValue(defaults.combatEntityAttacked)
                .setSaveConsumer(val -> config.combatEntityAttacked = val)
                .build());

        combat.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.combatPlayerDeath"), config.combatPlayerDeath)
                .setDefaultValue(defaults.combatPlayerDeath)
                .setSaveConsumer(val -> config.combatPlayerDeath = val)
                .build());

        combat.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.combatPlayerRespawn"), config.combatPlayerRespawn)
                .setDefaultValue(defaults.combatPlayerRespawn)
                .setSaveConsumer(val -> config.combatPlayerRespawn = val)
                .build());

        combat.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.combatNearDeath"), config.combatNearDeath)
                .setDefaultValue(defaults.combatNearDeath)
                .setSaveConsumer(val -> config.combatNearDeath = val)
                .build());

        combat.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.combatDamageTaken"), config.combatDamageTaken)
                .setDefaultValue(defaults.combatDamageTaken)
                .setSaveConsumer(val -> config.combatDamageTaken = val)
                .build());

        combat.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.combatShieldBlock"), config.combatShieldBlock)
                .setDefaultValue(defaults.combatShieldBlock)
                .setSaveConsumer(val -> config.combatShieldBlock = val)
                .build());

        combat.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.combatTotemPop"), config.combatTotemPop)
                .setDefaultValue(defaults.combatTotemPop)
                .setSaveConsumer(val -> config.combatTotemPop = val)
                .build());

        combat.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.combatLavaContact"), config.combatLavaContact)
                .setDefaultValue(defaults.combatLavaContact)
                .setSaveConsumer(val -> config.combatLavaContact = val)
                .build());

        combat.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.combatOnFire"), config.combatOnFire)
                .setDefaultValue(defaults.combatOnFire)
                .setSaveConsumer(val -> config.combatOnFire = val)
                .build());

        combat.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.combatDrowning"), config.combatDrowning)
                .setDefaultValue(defaults.combatDrowning)
                .setSaveConsumer(val -> config.combatDrowning = val)
                .build());

        // --- Boss Events ---
        ConfigCategory boss = builder.getOrCreateCategory(Component.translatable("config.obsannotator.category.boss"));

        boss.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enableBossEvents"), config.enableBossEvents)
                .setDefaultValue(defaults.enableBossEvents)
                .setSaveConsumer(val -> config.enableBossEvents = val)
                .build());

        boss.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.bossEnderDragonSpawned"), config.bossEnderDragonSpawned)
                .setDefaultValue(defaults.bossEnderDragonSpawned)
                .setSaveConsumer(val -> config.bossEnderDragonSpawned = val)
                .build());

        boss.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.bossEnderDragonDefeated"), config.bossEnderDragonDefeated)
                .setDefaultValue(defaults.bossEnderDragonDefeated)
                .setSaveConsumer(val -> config.bossEnderDragonDefeated = val)
                .build());

        boss.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.bossWitherSpawned"), config.bossWitherSpawned)
                .setDefaultValue(defaults.bossWitherSpawned)
                .setSaveConsumer(val -> config.bossWitherSpawned = val)
                .build());

        boss.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.bossWitherDefeated"), config.bossWitherDefeated)
                .setDefaultValue(defaults.bossWitherDefeated)
                .setSaveConsumer(val -> config.bossWitherDefeated = val)
                .build());

        // --- Block Events ---
        ConfigCategory block = builder.getOrCreateCategory(Component.translatable("config.obsannotator.category.block"));

        block.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enableBlockEvents"), config.enableBlockEvents)
                .setDefaultValue(defaults.enableBlockEvents)
                .setSaveConsumer(val -> config.enableBlockEvents = val)
                .build());

        block.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.blockBroken"), config.blockBroken)
                .setDefaultValue(defaults.blockBroken)
                .setSaveConsumer(val -> config.blockBroken = val)
                .build());

        block.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.blockPlaced"), config.blockPlaced)
                .setDefaultValue(defaults.blockPlaced)
                .setSaveConsumer(val -> config.blockPlaced = val)
                .build());

        // --- Item Events ---
        ConfigCategory item = builder.getOrCreateCategory(Component.translatable("config.obsannotator.category.item"));

        item.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enableItemEvents"), config.enableItemEvents)
                .setDefaultValue(defaults.enableItemEvents)
                .setSaveConsumer(val -> config.enableItemEvents = val)
                .build());

        item.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.itemRareObtained"), config.itemRareObtained)
                .setDefaultValue(defaults.itemRareObtained)
                .setSaveConsumer(val -> config.itemRareObtained = val)
                .build());

        item.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.itemUsed"), config.itemUsed)
                .setDefaultValue(defaults.itemUsed)
                .setSaveConsumer(val -> config.itemUsed = val)
                .build());

        item.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.foodEaten"), config.foodEaten)
                .setDefaultValue(defaults.foodEaten)
                .setSaveConsumer(val -> config.foodEaten = val)
                .build());

        item.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.potionDrunk"), config.potionDrunk)
                .setDefaultValue(defaults.potionDrunk)
                .setSaveConsumer(val -> config.potionDrunk = val)
                .build());

        item.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.bowFired"), config.bowFired)
                .setDefaultValue(defaults.bowFired)
                .setSaveConsumer(val -> config.bowFired = val)
                .build());

        item.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enderPearlThrown"), config.enderPearlThrown)
                .setDefaultValue(defaults.enderPearlThrown)
                .setSaveConsumer(val -> config.enderPearlThrown = val)
                .build());

        item.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.itemToolBroke"), config.itemToolBroke)
                .setDefaultValue(defaults.itemToolBroke)
                .setSaveConsumer(val -> config.itemToolBroke = val)
                .build());

        // --- Exploration Events ---
        ConfigCategory exploration = builder.getOrCreateCategory(Component.translatable("config.obsannotator.category.exploration"));

        exploration.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enableExplorationEvents"), config.enableExplorationEvents)
                .setDefaultValue(defaults.enableExplorationEvents)
                .setSaveConsumer(val -> config.enableExplorationEvents = val)
                .build());

        exploration.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.explorationNewBiome"), config.explorationNewBiome)
                .setDefaultValue(defaults.explorationNewBiome)
                .setSaveConsumer(val -> config.explorationNewBiome = val)
                .build());

        exploration.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.explorationBiomeChanged"), config.explorationBiomeChanged)
                .setDefaultValue(defaults.explorationBiomeChanged)
                .setSaveConsumer(val -> config.explorationBiomeChanged = val)
                .build());

        exploration.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.explorationStructureEntered"), config.explorationStructureEntered)
                .setDefaultValue(defaults.explorationStructureEntered)
                .setSaveConsumer(val -> config.explorationStructureEntered = val)
                .build());

        exploration.addEntry(entry.startIntField(Component.translatable("config.obsannotator.biomeChangeCooldown"), config.biomeChangeCooldown)
                .setDefaultValue(defaults.biomeChangeCooldown)
                .setMin(0)
                .setSaveConsumer(val -> config.biomeChangeCooldown = val)
                .setTooltip(Component.translatable("config.obsannotator.biomeChangeCooldown.tooltip"))
                .build());

        // --- Achievement Events ---
        ConfigCategory achievement = builder.getOrCreateCategory(Component.translatable("config.obsannotator.category.achievement"));

        achievement.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enableAchievementEvents"), config.enableAchievementEvents)
                .setDefaultValue(defaults.enableAchievementEvents)
                .setSaveConsumer(val -> config.enableAchievementEvents = val)
                .build());

        achievement.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.achievementUnlocked"), config.achievementUnlocked)
                .setDefaultValue(defaults.achievementUnlocked)
                .setSaveConsumer(val -> config.achievementUnlocked = val)
                .build());

        // --- Fall Events ---
        ConfigCategory fall = builder.getOrCreateCategory(Component.translatable("config.obsannotator.category.fall"));

        fall.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enableFallEvents"), config.enableFallEvents)
                .setDefaultValue(defaults.enableFallEvents)
                .setSaveConsumer(val -> config.enableFallEvents = val)
                .build());

        fall.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.fallLanded"), config.fallLanded)
                .setDefaultValue(defaults.fallLanded)
                .setSaveConsumer(val -> config.fallLanded = val)
                .build());

        fall.addEntry(entry.startIntField(Component.translatable("config.obsannotator.fallMinDurationMs"), config.fallMinDurationMs)
                .setDefaultValue(defaults.fallMinDurationMs)
                .setMin(0)
                .setSaveConsumer(val -> config.fallMinDurationMs = val)
                .setTooltip(Component.translatable("config.obsannotator.fallMinDurationMs.tooltip"))
                .build());

        // --- Explosion Events ---
        ConfigCategory explosion = builder.getOrCreateCategory(Component.translatable("config.obsannotator.category.explosion"));

        explosion.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enableExplosionEvents"), config.enableExplosionEvents)
                .setDefaultValue(defaults.enableExplosionEvents)
                .setSaveConsumer(val -> config.enableExplosionEvents = val)
                .build());

        explosion.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.explosionTnt"), config.explosionTnt)
                .setDefaultValue(defaults.explosionTnt)
                .setSaveConsumer(val -> config.explosionTnt = val)
                .build());

        explosion.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.explosionEndCrystal"), config.explosionEndCrystal)
                .setDefaultValue(defaults.explosionEndCrystal)
                .setSaveConsumer(val -> config.explosionEndCrystal = val)
                .build());

        explosion.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.explosionBed"), config.explosionBed)
                .setDefaultValue(defaults.explosionBed)
                .setSaveConsumer(val -> config.explosionBed = val)
                .build());

        explosion.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.explosionOther"), config.explosionOther)
                .setDefaultValue(defaults.explosionOther)
                .setSaveConsumer(val -> config.explosionOther = val)
                .build());

        explosion.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.explosionTntIgnited"), config.explosionTntIgnited)
                .setDefaultValue(defaults.explosionTntIgnited)
                .setSaveConsumer(val -> config.explosionTntIgnited = val)
                .build());

        // --- Interaction Events ---
        ConfigCategory interaction = builder.getOrCreateCategory(Component.translatable("config.obsannotator.category.interaction"));

        interaction.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enableInteractionEvents"), config.enableInteractionEvents)
                .setDefaultValue(defaults.enableInteractionEvents)
                .setSaveConsumer(val -> config.enableInteractionEvents = val)
                .build());

        interaction.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.interactionCrafting"), config.interactionCrafting)
                .setDefaultValue(defaults.interactionCrafting)
                .setSaveConsumer(val -> config.interactionCrafting = val)
                .build());

        interaction.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.interactionTrading"), config.interactionTrading)
                .setDefaultValue(defaults.interactionTrading)
                .setSaveConsumer(val -> config.interactionTrading = val)
                .build());

        interaction.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.interactionEnchanting"), config.interactionEnchanting)
                .setDefaultValue(defaults.interactionEnchanting)
                .setSaveConsumer(val -> config.interactionEnchanting = val)
                .build());

        interaction.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.interactionPortal"), config.interactionPortal)
                .setDefaultValue(defaults.interactionPortal)
                .setSaveConsumer(val -> config.interactionPortal = val)
                .build());

        interaction.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.interactionSleep"), config.interactionSleep)
                .setDefaultValue(defaults.interactionSleep)
                .setSaveConsumer(val -> config.interactionSleep = val)
                .build());

        interaction.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.interactionBeacon"), config.interactionBeacon)
                .setDefaultValue(defaults.interactionBeacon)
                .setSaveConsumer(val -> config.interactionBeacon = val)
                .build());

        // --- Movement Events ---
        ConfigCategory movement = builder.getOrCreateCategory(Component.translatable("config.obsannotator.category.movement"));

        movement.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enableMovementEvents"), config.enableMovementEvents)
                .setDefaultValue(defaults.enableMovementEvents)
                .setSaveConsumer(val -> config.enableMovementEvents = val)
                .build());

        movement.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.movementElytraStart"), config.movementElytraStart)
                .setDefaultValue(defaults.movementElytraStart)
                .setSaveConsumer(val -> config.movementElytraStart = val)
                .build());

        movement.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.movementElytraLand"), config.movementElytraLand)
                .setDefaultValue(defaults.movementElytraLand)
                .setSaveConsumer(val -> config.movementElytraLand = val)
                .build());

        movement.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.movementMountRide"), config.movementMountRide)
                .setDefaultValue(defaults.movementMountRide)
                .setSaveConsumer(val -> config.movementMountRide = val)
                .build());

        movement.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.movementMountDismount"), config.movementMountDismount)
                .setDefaultValue(defaults.movementMountDismount)
                .setSaveConsumer(val -> config.movementMountDismount = val)
                .build());

        // --- Environment Events ---
        ConfigCategory environment = builder.getOrCreateCategory(Component.translatable("config.obsannotator.category.environment"));

        environment.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enableEnvironmentEvents"), config.enableEnvironmentEvents)
                .setDefaultValue(defaults.enableEnvironmentEvents)
                .setSaveConsumer(val -> config.enableEnvironmentEvents = val)
                .build());

        environment.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.environmentLightning"), config.environmentLightning)
                .setDefaultValue(defaults.environmentLightning)
                .setSaveConsumer(val -> config.environmentLightning = val)
                .build());

        environment.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.environmentRaid"), config.environmentRaid)
                .setDefaultValue(defaults.environmentRaid)
                .setSaveConsumer(val -> config.environmentRaid = val)
                .build());

        environment.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.environmentWardenSummoned"), config.environmentWardenSummoned)
                .setDefaultValue(defaults.environmentWardenSummoned)
                .setSaveConsumer(val -> config.environmentWardenSummoned = val)
                .build());

        // --- Status Effect Events ---
        ConfigCategory statusEffect = builder.getOrCreateCategory(Component.translatable("config.obsannotator.category.statusEffect"));

        statusEffect.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.enableStatusEffectEvents"), config.enableStatusEffectEvents)
                .setDefaultValue(defaults.enableStatusEffectEvents)
                .setSaveConsumer(val -> config.enableStatusEffectEvents = val)
                .build());

        statusEffect.addEntry(entry.startBooleanToggle(Component.translatable("config.obsannotator.statusEffectApplied"), config.statusEffectApplied)
                .setDefaultValue(defaults.statusEffectApplied)
                .setSaveConsumer(val -> config.statusEffectApplied = val)
                .build());

        return builder.build();
    }
}
