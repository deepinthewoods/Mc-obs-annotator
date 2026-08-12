# OBS Annotator

A Minecraft Fabric mod that automatically sends annotations to [StreamUP Chapter Marker Manager](https://github.com/StreamUPTips/obs-chapter-marker-manager) for OBS when gameplay events occur.

## Features

### Manual Keybinds
- **Start** (Default: Numpad 7) - Mark a start point
- **End** (Default: Numpad 9) - Mark an end point
- **POI A** (Default: Numpad 4) - Mark point of interest A
- **POI B** (Default: Numpad 6) - Mark point of interest B

All keybinds are remappable through Minecraft's controls menu under the "OBS Annotator" category.

### Automatic Event Tracking

The mod automatically sends annotations for the following events:

#### Combat Events (5)
- Entity Attacked
- Player Death
- Player Respawn
- Near Death (health below 2 hearts)
- Damage Taken

#### Boss Events (4)
- Ender Dragon Spawned
- Ender Dragon Defeated
- Wither Spawned
- Wither Defeated

#### Block Events (3)
- Block Broken (deduplicated - skips if same block broken in same tick)
- Block Left Click
- Block Right Click

#### Item Events (2)
- Rare Item Obtained (diamonds, netherite, ancient debris, enchanted books)
- Item Used

#### Exploration Events (3)
- New Biome Type (first time visiting a biome type)
- Biome Changed (5 second cooldown)
- Structure Entered

#### Achievement Events (1)
- Achievement Unlocked

#### Fall Damage (1)
- High Fall Damage (4+ damage)

#### Explosion Events (1)
- Explosion Detected (TNT, beds, end crystals, creepers, etc.)

## Installation

### Requirements
- Minecraft 1.21.10
- Fabric Loader 0.17.3+
- Fabric API
- [StreamUP Chapter Marker Manager](https://obsproject.com/forum/resources/streamup-chapter-marker-manager.1962/) installed in OBS

### Steps
1. Install Fabric Loader for Minecraft 1.21.10
2. Download and install Fabric API
3. Place this mod's JAR file in your `.minecraft/mods` folder
4. Install StreamUP Chapter Marker Manager in OBS
5. Start OBS and ensure the Chapter Marker Manager is running
6. Launch Minecraft

## Configuration

The mod creates a configuration file at `.minecraft/config/obsannotator.json` on first run.

### OBS WebSocket Settings
```json
{
  "obsHost": "localhost",
  "obsPort": 4455,
  "obsPassword": ""
}
```

- **obsHost**: The host where OBS WebSocket is running (default: localhost)
- **obsPort**: The WebSocket port (default: 4455)
- **obsPassword**: OBS WebSocket password if authentication is enabled

### Event Toggles

You can enable/disable entire event categories:
- `enableCombatEvents`
- `enableBossEvents`
- `enableBlockEvents`
- `enableItemEvents`
- `enableExplorationEvents`
- `enableAchievementEvents`
- `enableFallDamageEvents`
- `enableExplosionEvents`

Individual events can also be toggled. For example:
- `combatEntityAttacked`
- `bossEnderDragonSpawned`
- `blockBroken`
- etc.

### Cooldown Settings
- `biomeChangeCooldown`: Milliseconds between biome change annotations (default: 5000)

## How It Works

1. The mod connects to OBS via WebSocket when Minecraft starts
2. When configured events occur in-game, annotations are sent to StreamUP Chapter Marker Manager
3. StreamUP records these annotations as chapter markers in your OBS recording
4. After recording, you can export markers for easier video editing

## Multiplayer Support

This mod works in multiplayer and only tracks events related to the local player.

## Troubleshooting

### Mod not connecting to OBS
- Ensure OBS is running with StreamUP Chapter Marker Manager installed
- Check that OBS WebSocket is enabled and running on port 4455
- Verify the password in the config file matches your OBS WebSocket password
- Check Minecraft logs for connection errors

### Too many annotations
- Disable spammy events in the config file (e.g., `blockLeftClick`, `itemUsed`)
- Disable entire event categories you don't need
- Increase the `biomeChangeCooldown` for exploration events

### Annotations not appearing in OBS
- Ensure you have an active recording in OBS
- Check that StreamUP Chapter Marker Manager is properly installed
- Verify the mod shows "Successfully authenticated with OBS" in the log

## License

CC0-1.0

## Links

- [StreamUP Chapter Marker Manager](https://github.com/StreamUPTips/obs-chapter-marker-manager)
- [Fabric Mod Development](https://fabricmc.net/)
