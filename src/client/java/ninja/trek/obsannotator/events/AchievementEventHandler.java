package ninja.trek.obsannotator.events;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.advancements.AdvancementProgress;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientAdvancements;
import net.minecraft.client.player.LocalPlayer;
import ninja.trek.obsannotator.ObsAnnotatorClient;
import ninja.trek.obsannotator.mixin.client.ClientAdvancementsAccessor;

import java.util.HashMap;
import java.util.Map;

public class AchievementEventHandler {
    private static final Map<AdvancementHolder, Boolean> trackedAdvancements = new HashMap<>();

    public static void register() {
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            LocalPlayer player = client.player;
            if (player == null ||
                !ObsAnnotatorClient.CONFIG.enableAchievementEvents ||
                !ObsAnnotatorClient.CONFIG.achievementUnlocked) {
                return;
            }

            ClientAdvancements advancements = client.player.connection.getAdvancements();

            // Check all advancements for completion
            // Note: Using accessor to get progress map
            for (Map.Entry<AdvancementHolder, AdvancementProgress> entry : ((ClientAdvancementsAccessor) advancements).getProgress().entrySet()) {
                AdvancementHolder advancement = entry.getKey();
                AdvancementProgress progress = entry.getValue();

                boolean wasCompleted = trackedAdvancements.getOrDefault(advancement, false);
                boolean isCompleted = progress.isDone();

                // Advancement was just completed
                if (isCompleted && !wasCompleted) {
                    ObsAnnotatorClient.sendAnnotation("Achievement - Unlocked");
                }

                trackedAdvancements.put(advancement, isCompleted);
            }
        });
    }
}
