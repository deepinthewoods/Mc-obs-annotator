package ninja.trek.obsannotator;

import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;

import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Tracks event state for deduplication and cooldowns
 */
public class EventTracker {
    // Near-death tracking
    private boolean wasNearDeath = false;

    // Block break deduplication (last tick)
    private Block lastBrokenBlock = null;

    // Biome tracking
    private final Set<ResourceKey<Biome>> visitedBiomes = new HashSet<>();
    private ResourceKey<Biome> currentBiome = null;
    private long lastBiomeChangeTime = 0;

    // Structure tracking
    private final Set<String> currentStructures = new HashSet<>();

    // Annotation cooldown tracking (prevents duplicate sends within cooldown window)
    private final Map<String, Long> lastAnnotationTime = new ConcurrentHashMap<>();
    private static final long DEFAULT_COOLDOWN_MS = 50; // 1 tick = 50ms

    // Fall tracking
    private long fallStartTick = -1;
    private boolean wasFalling = false;

    // Portal / dimension tracking
    private ResourceKey<?> lastDimension = null;

    // Sleep tracking
    private boolean wasSleeping = false;

    // Elytra tracking
    private boolean wasElytraFlying = false;

    // Mount tracking
    private Entity lastVehicle = null;

    // Damage state tracking
    private boolean wasInLava = false;
    private boolean wasOnFire = false;
    private boolean wasDrowning = false;

    // Status effect tracking
    private Set<Holder<MobEffect>> lastActiveEffects = new HashSet<>();

    // Tool break tracking
    private ItemStack lastHeldItemStack = ItemStack.EMPTY;
    private int lastHeldItemDurability = 0;

    // Entity UUID tracking (lightning, warden)
    private final Set<UUID> trackedWardenUUIDs = new HashSet<>();
    private final Set<UUID> trackedLightningUUIDs = new HashSet<>();

    // Shield blocking tracking
    private boolean wasShieldBlocking = false;

    // Totem pop tracking
    private float previousTickHealth = -1;

    public boolean shouldTriggerNearDeath(boolean isNearDeath) {
        if (isNearDeath && !wasNearDeath) {
            wasNearDeath = true;
            return true;
        } else if (!isNearDeath) {
            wasNearDeath = false;
        }
        return false;
    }

    public boolean shouldTriggerBlockBreak(Block block) {
        if (block == lastBrokenBlock) {
            return false;
        }
        lastBrokenBlock = block;
        return true;
    }

    public void resetBlockBreakTracking() {
        lastBrokenBlock = null;
    }

    public boolean isNewBiome(ResourceKey<Biome> biome) {
        return visitedBiomes.add(biome);
    }

    public boolean shouldTriggerBiomeChange(ResourceKey<Biome> biome, long currentTime, int cooldownMs) {
        if (biome.equals(currentBiome)) {
            return false;
        }

        if (currentTime - lastBiomeChangeTime < cooldownMs) {
            return false;
        }

        currentBiome = biome;
        lastBiomeChangeTime = currentTime;
        return true;
    }

    public boolean shouldTriggerStructureEnter(String structureId) {
        return currentStructures.add(structureId);
    }

    public void leaveStructure(String structureId) {
        currentStructures.remove(structureId);
    }

    /**
     * Returns true if enough time has passed since the last annotation with the same key.
     * Use this to prevent duplicate annotations from callbacks that fire multiple times
     * per player action (e.g. once per hand).
     */
    public boolean shouldTriggerAnnotation(String annotationKey) {
        long now = System.currentTimeMillis();
        Long lastTime = lastAnnotationTime.get(annotationKey);
        if (lastTime != null && (now - lastTime) < DEFAULT_COOLDOWN_MS) {
            return false;
        }
        lastAnnotationTime.put(annotationKey, now);
        return true;
    }

    // --- Fall tracking ---

    public void startFalling(long tick) {
        if (!wasFalling) {
            fallStartTick = tick;
            wasFalling = true;
        }
    }

    /**
     * Called when player lands. Returns fall duration in ticks, or -1 if not falling or below threshold.
     */
    public long landedFromFall(long currentTick, int minDurationMs) {
        if (!wasFalling || fallStartTick < 0) {
            wasFalling = false;
            return -1;
        }
        long durationTicks = currentTick - fallStartTick;
        long durationMs = durationTicks * 50; // 1 tick = 50ms
        wasFalling = false;
        fallStartTick = -1;
        if (durationMs >= minDurationMs) {
            return durationTicks;
        }
        return -1;
    }

    public boolean wasFalling() {
        return wasFalling;
    }

    public void cancelFall() {
        wasFalling = false;
        fallStartTick = -1;
    }

    // --- Dimension tracking ---

    public ResourceKey<?> getLastDimension() {
        return lastDimension;
    }

    public void setLastDimension(ResourceKey<?> dimension) {
        this.lastDimension = dimension;
    }

    // --- Sleep tracking ---

    public boolean wasSleeping() {
        return wasSleeping;
    }

    public void setWasSleeping(boolean sleeping) {
        this.wasSleeping = sleeping;
    }

    // --- Elytra tracking ---

    public boolean wasElytraFlying() {
        return wasElytraFlying;
    }

    public void setWasElytraFlying(boolean flying) {
        this.wasElytraFlying = flying;
    }

    // --- Mount tracking ---

    public Entity getLastVehicle() {
        return lastVehicle;
    }

    public void setLastVehicle(Entity vehicle) {
        this.lastVehicle = vehicle;
    }

    // --- Damage state tracking ---

    public boolean wasInLava() {
        return wasInLava;
    }

    public void setWasInLava(boolean inLava) {
        this.wasInLava = inLava;
    }

    public boolean wasOnFire() {
        return wasOnFire;
    }

    public void setWasOnFire(boolean onFire) {
        this.wasOnFire = onFire;
    }

    public boolean wasDrowning() {
        return wasDrowning;
    }

    public void setWasDrowning(boolean drowning) {
        this.wasDrowning = drowning;
    }

    // --- Status effect tracking ---

    public Set<Holder<MobEffect>> getLastActiveEffects() {
        return lastActiveEffects;
    }

    public void setLastActiveEffects(Set<Holder<MobEffect>> effects) {
        this.lastActiveEffects = new HashSet<>(effects);
    }

    // --- Tool break tracking ---

    public ItemStack getLastHeldItemStack() {
        return lastHeldItemStack;
    }

    public void setLastHeldItemStack(ItemStack stack) {
        this.lastHeldItemStack = stack.copy();
    }

    public int getLastHeldItemDurability() {
        return lastHeldItemDurability;
    }

    public void setLastHeldItemDurability(int durability) {
        this.lastHeldItemDurability = durability;
    }

    // --- Entity UUID tracking ---

    public boolean isNewWarden(UUID uuid) {
        return trackedWardenUUIDs.add(uuid);
    }

    public boolean isNewLightning(UUID uuid) {
        return trackedLightningUUIDs.add(uuid);
    }

    // --- Shield tracking ---

    public boolean wasShieldBlocking() {
        return wasShieldBlocking;
    }

    public void setWasShieldBlocking(boolean blocking) {
        this.wasShieldBlocking = blocking;
    }

    // --- Totem pop tracking ---

    public float getPreviousTickHealth() {
        return previousTickHealth;
    }

    public void setPreviousTickHealth(float health) {
        this.previousTickHealth = health;
    }

    public void reset() {
        wasNearDeath = false;
        lastBrokenBlock = null;
        currentStructures.clear();
        lastAnnotationTime.clear();
        wasFalling = false;
        fallStartTick = -1;
        lastDimension = null;
        wasSleeping = false;
        wasElytraFlying = false;
        lastVehicle = null;
        wasInLava = false;
        wasOnFire = false;
        wasDrowning = false;
        lastActiveEffects.clear();
        lastHeldItemStack = ItemStack.EMPTY;
        lastHeldItemDurability = 0;
        trackedWardenUUIDs.clear();
        trackedLightningUUIDs.clear();
        wasShieldBlocking = false;
        previousTickHealth = -1;
    }
}
