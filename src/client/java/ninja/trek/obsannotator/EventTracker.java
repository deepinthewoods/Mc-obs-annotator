package ninja.trek.obsannotator;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

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

    public void reset() {
        wasNearDeath = false;
        lastBrokenBlock = null;
        currentStructures.clear();
    }
}
