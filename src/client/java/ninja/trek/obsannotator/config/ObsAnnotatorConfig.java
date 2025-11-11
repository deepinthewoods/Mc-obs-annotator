package ninja.trek.obsannotator.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import net.fabricmc.loader.api.FabricLoader;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;

public class ObsAnnotatorConfig {
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private static final Path CONFIG_PATH = FabricLoader.getInstance().getConfigDir().resolve("obsannotator.json");

    private static FileTime lastModifiedTime = null;

    // OBS WebSocket Connection Settings
    public String obsHost = "localhost";
    public int obsPort = 4455;
    public String obsPassword = "";

    // Event Toggle Settings
    public boolean enableCombatEvents = true;
    public boolean enableBossEvents = true;
    public boolean enableBlockEvents = true;
    public boolean enableItemEvents = true;
    public boolean enableExplorationEvents = true;
    public boolean enableAchievementEvents = true;
    public boolean enableFallDamageEvents = true;
    public boolean enableExplosionEvents = true;

    // Individual Event Toggles
    public boolean combatEntityAttacked = true;
    public boolean combatPlayerDeath = true;
    public boolean combatPlayerRespawn = true;
    public boolean combatNearDeath = true;
    public boolean combatDamageTaken = true;

    public boolean bossEnderDragonSpawned = true;
    public boolean bossEnderDragonDefeated = true;
    public boolean bossWitherSpawned = true;
    public boolean bossWitherDefeated = true;

    public boolean blockBroken = true;
    public boolean blockLeftClick = true;
    public boolean blockRightClick = true;

    public boolean itemRareObtained = true;
    public boolean itemUsed = true;

    public boolean explorationNewBiome = true;
    public boolean explorationBiomeChanged = true;
    public boolean explorationStructureEntered = true;

    public boolean achievementUnlocked = true;

    public boolean fallHighDamage = true;

    public boolean explosionTnt = true;
    public boolean explosionEndCrystal = true;
    public boolean explosionBed = true;
    public boolean explosionOther = true;

    // Cooldown settings (in milliseconds)
    public int biomeChangeCooldown = 5000;

    public static ObsAnnotatorConfig load() {
        if (Files.exists(CONFIG_PATH)) {
            try {
                lastModifiedTime = Files.getLastModifiedTime(CONFIG_PATH);
                String json = Files.readString(CONFIG_PATH);
                return GSON.fromJson(json, ObsAnnotatorConfig.class);
            } catch (IOException e) {
                System.err.println("Failed to load OBS Annotator config, using defaults: " + e.getMessage());
            }
        }

        // Create default config
        ObsAnnotatorConfig config = new ObsAnnotatorConfig();
        config.save();
        try {
            lastModifiedTime = Files.getLastModifiedTime(CONFIG_PATH);
        } catch (IOException e) {
            // Ignore
        }
        return config;
    }

    public void save() {
        try {
            Files.createDirectories(CONFIG_PATH.getParent());
            Files.writeString(CONFIG_PATH, GSON.toJson(this));
        } catch (IOException e) {
            System.err.println("Failed to save OBS Annotator config: " + e.getMessage());
        }
    }

    public static boolean hasConfigFileChanged() {
        if (!Files.exists(CONFIG_PATH)) {
            return false;
        }

        try {
            FileTime currentModifiedTime = Files.getLastModifiedTime(CONFIG_PATH);
            return lastModifiedTime == null || currentModifiedTime.compareTo(lastModifiedTime) > 0;
        } catch (IOException e) {
            return false;
        }
    }

    public static Path getConfigPath() {
        return CONFIG_PATH;
    }
}
