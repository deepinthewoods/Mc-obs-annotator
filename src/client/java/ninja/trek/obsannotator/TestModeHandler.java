package ninja.trek.obsannotator;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;

import java.util.List;

public class TestModeHandler {

    private static boolean joined = false;
    private static int markerIndex = 0;
    private static boolean done = false;

    private static final List<String> MARKERS = List.of(
        "Start",
        "End",
        "POI A",
        "POI B",
        "Entity Attacked - Zombie",
        "Combat - Player Death",
        "Combat - Player Respawn",
        "Combat - Totem of Undying",
        "Combat - Damage Taken",
        "Combat - Shield Block",
        "Combat - Near Death",
        "Damage - Lava Contact",
        "Damage - On Fire",
        "Damage - Drowning",
        "Boss - Ender Dragon Spawned",
        "Boss - Ender Dragon Defeated",
        "Boss - Wither Spawned",
        "Boss - Wither Defeated",
        "Block Break - Diamond Ore",
        "Block Place - Stone",
        "Rare Item - Diamond",
        "Food Eaten - Golden Apple",
        "Potion Drunk - Healing",
        "Bow Fired",
        "Crossbow Fired",
        "Trident Thrown",
        "Ender Pearl Thrown",
        "Item Used - Shield",
        "Item - Tool Broke (Diamond Pickaxe)",
        "Exploration - New Biome Type",
        "Exploration - Biome Changed",
        "Achievement - Unlocked",
        "Explosion - TNT Ignited",
        "Explosion - Other",
        "Fall Landed (3.5s)",
        "Crafted - Diamond Sword",
        "Trade Completed",
        "Enchanted - Diamond Sword",
        "Entered Nether",
        "Entered End",
        "Returned to Overworld",
        "Dimension Changed",
        "Interaction - Beacon Activated",
        "Started Sleeping",
        "Woke Up",
        "Elytra - Started Flying",
        "Elytra - Landed",
        "Mount - Riding Horse",
        "Mount - Dismounted",
        "Environment - Lightning Strike",
        "Environment - Warden Summoned",
        "Environment - Raid Started",
        "Status Effect - Speed"
    );

    public static boolean isTestMode() {
        return "true".equals(System.getProperty("obs.annotator.testmode"));
    }

    public static void register() {
        ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> {
            joined = true;
            markerIndex = 0;
            done = false;
            System.out.println("[OBS Annotator] Test mode: player joined, starting marker sequence (" + MARKERS.size() + " markers)");
        });

        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            if (!joined || done) return;

            if (markerIndex < MARKERS.size()) {
                String marker = MARKERS.get(markerIndex);
                System.out.println("[OBS Annotator] Test mode: sending marker [" + (markerIndex + 1) + "/" + MARKERS.size() + "] " + marker);
                ObsAnnotatorClient.sendAnnotation(marker);
                markerIndex++;
            } else {
                done = true;
                System.out.println("[OBS Annotator] Test mode: all " + MARKERS.size() + " markers sent.");
            }
        });
    }
}
