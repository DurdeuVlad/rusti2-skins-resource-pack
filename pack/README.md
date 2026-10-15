# Custom NPC Skins and Sounds

Resource-pack skeleton for Minecraft Java 1.21.1, NeoForge, and
CustomNPCs-Unofficial. Minecraft 1.21 and 1.21.1 use resource-pack format 34.

## Folder map

```text
Custom NPC resource pack/
|-- pack.mcmeta
|-- pack.png                              optional 128 x 128 pack icon
`-- assets/
    `-- customnpcs/
        |-- sounds.json                   registers every custom sound event
        |-- lang/
        |   `-- en_us.json                subtitle text
        |-- textures/
        |   `-- entity/
        |       `-- custom/
        |           `-- your_npc.png      put NPC skins here
        `-- sounds/
            `-- custom/
                |-- voice/
                |   `-- greeting_01.ogg   short voice lines
                |-- ambient/
                |   `-- tavern_loop.ogg   long/looping ambience or music
                `-- sfx/
                    `-- quest_complete.ogg short sound effects
```

The folder named `customnpcs` is intentional. It makes the resources part of
the mod's namespace and gives the Custom NPC texture picker the best chance of
listing them. Keep every folder and file name below `assets` lowercase; use
underscores instead of spaces.

## Add a skin

1. Export a standard Java Edition skin as a PNG. A modern player-style skin is
   normally 64 x 64 pixels. Other NPC models may require a texture matching that
   model's UV layout.
2. Put it in `assets/customnpcs/textures/entity/custom/`, for example:
   `assets/customnpcs/textures/entity/custom/village_guard.png`.
3. Reload resources with `F3 + T`, or restart Minecraft.
4. Edit the NPC with the NPC Wand. Under **Display -> Texture**, use the Select
   button and browse to the `custom` folder. If the picker requires a typed
   resource location, use:

   `customnpcs:textures/entity/custom/village_guard.png`

The texture is client-side. Every multiplayer player must receive/enable this
resource pack or they will see a missing texture.

## Included skin library

The imported library is under
`assets/customnpcs/textures/entity/custom/skinuri_sortate_toate/` and contains
all 296 images from `skinuri sortate toate.zip`:

- `slim/` contains 3-pixel-arm (Alex-style) player skins.
- `wide/` contains 4-pixel-arm (Steve-style) player skins.
- Each model folder has a `premium/` subfolder matching the source archive.
- `mobs/<entity>/` contains textures for that exact entity model.

Choose the matching player model before selecting a texture. The source ZIP's
Alex/Steve folders are used as the baseline, then checked against the actual UV
layout. Four incorrectly sorted source files have conclusive missing arm faces and
are placed under the model they really fit.

The source ZIP's `skinuri mobi` branch is included under `mobs/`. Select the
matching entity model before applying one of those textures; putting a wolf,
blaze, villager, or other entity UV on a player-shaped NPC will render as
scrambled body parts. The source's `infernal_fox` and `doge_skin` files are
placed under `mobs/wolf` because their 64 x 32 UV layouts are wolf textures,
not the 48 x 32 fox layout.

`SKIN_CATALOG.csv` is the authoritative lookup table for all 161 player skins
and 135 entity textures. Its `RequiredModel` column says which model to select and its
`ResourceLocation` column can be copied directly into CustomNPCs.

All player skins are usable PNGs. Five legacy 64 x 32 player skins were
converted to the modern 64 x 64 layout, invalid transparent holes in five base
layers were filled, and the two WebP player skins were converted to PNG.
`SKIN_IMPORT_MANIFEST.csv` records the action and final path for every source
image. Exact source duplicates are retained under distinct resource names.

## Add a sound

Minecraft requires Ogg Vorbis (`.ogg`), not a renamed MP3 or WAV. Use mono audio
for NPC voices and positional effects so distance attenuation works correctly.
Stereo is suitable for non-positional music, but it will not behave like a
sound located at the NPC.

Three ready-made sound events are registered in `assets/customnpcs/sounds.json`:

| Sound event ID | Put this file here | Intended use |
| --- | --- | --- |
| `customnpcs:custom.npc.greeting` | `assets/customnpcs/sounds/custom/voice/greeting_01.ogg` | Short NPC voice |
| `customnpcs:custom.ambient.tavern` | `assets/customnpcs/sounds/custom/ambient/tavern_loop.ogg` | Long streamed ambience/music |
| `customnpcs:custom.sfx.quest_complete` | `assets/customnpcs/sounds/custom/sfx/quest_complete.ogg` | Short effect |

After adding the `.ogg` files, reload with `F3 + T`. Test an event with:

```mcfunction
/playsound customnpcs:custom.npc.greeting voice @s ~ ~ ~ 1 1
```

In a Custom NPC sound field, use the full event ID, such as
`customnpcs:custom.npc.greeting`. Depending on the particular editor screen,
the event may appear in a picker after a resource reload or may need to be typed.

The example voice event contains only `greeting_01`. To give it random variants,
add files such as `greeting_02.ogg` and list them in the same `sounds` array:

```json
"custom.npc.greeting": {
  "subtitle": "subtitles.customnpcs.custom.npc.greeting",
  "sounds": [
    "customnpcs:custom/voice/greeting_01",
    "customnpcs:custom/voice/greeting_02"
  ]
}
```

Do not include `.ogg` in a sound name inside `sounds.json`.

## Install the pack

For one player, copy this entire folder into the Minecraft instance's
`resourcepacks` folder, then enable it under **Options -> Resource Packs**.

If you zip it, `pack.mcmeta` and `assets` must be at the top level of the ZIP;
do not leave them inside an extra wrapper folder. For a server, distribute the
same ZIP as the server resource pack. The CustomNPCs mod itself is still needed
on both client and server where required by the modpack.

## Add more sound events

Copy an existing block in `sounds.json`, add a comma between blocks, then change
both the event key and file path. Keep JSON syntax exact: double quotes, no
comments, and no trailing comma after the final block.

For short voice/SFX entries, omit `stream` or set it to `false`. For long music
or ambience, set `stream` to `true` so Minecraft streams it instead of loading
the entire file into memory.

## Common problems

- Pink/black NPC: the texture path or filename is wrong, the pack is disabled,
  or the PNG does not match the selected NPC model.
- Sound event is unknown: `sounds.json` is invalid or the event ID was typed
  without the `customnpcs:` namespace.
- Event exists but is silent: the referenced `.ogg` is missing, is not Vorbis,
  or its name/capitalization does not exactly match `sounds.json`.
- Pack does not appear: confirm the file is named exactly `pack.mcmeta` and that
  it is directly beside the `assets` folder.
