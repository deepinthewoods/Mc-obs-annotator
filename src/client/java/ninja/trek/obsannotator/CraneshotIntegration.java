package ninja.trek.obsannotator;

/**
 * Detects Minecraft processes launched as Craneshot followers without taking
 * a compile-time dependency on the Craneshot mod.
 */
public final class CraneshotIntegration {
    private static final String FOLLOWER_PROPERTY = "craneshot.follower";

    private CraneshotIntegration() {
    }

    /**
     * A supplied property means this process is a follower. The index may be
     * zero, so property presence—not its numeric value—is the important part.
     */
    public static boolean isFollower() {
        return System.getProperty(FOLLOWER_PROPERTY) != null;
    }

    /**
     * Returns a stable marker label such as "Craneshot Follower 0".
     */
    public static String getFollowerInstanceName() {
        String index = System.getProperty(FOLLOWER_PROPERTY);
        if (index == null) {
            return null;
        }

        index = index.trim();
        return index.isEmpty() ? "Craneshot Follower" : "Craneshot Follower " + index;
    }
}
