#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()


def read(rel):
    return (root / rel).read_text(encoding='utf-8')


def write(rel, s):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding='utf-8')
    print('patched', rel)


def replace_once(s, old, new, label):
    if old not in s:
        raise RuntimeError(f'Expected block not found: {label}')
    return s.replace(old, new, 1)

# ---------------- Settings / Stonecutter ----------------
s = read('settings.gradle')
s = replace_once(s,
'''        vers("1.20.1-fabric", "1.20.1")\n''',
'''        vers("1.20.1-fabric", "1.20.1")\n        vers("1.20.1-forge", "1.20.1")\n''', 'settings 1.20.1 forge target')
write('settings.gradle', s)

s = read('stonecutter.gradle.kts')
s = replace_once(s, 'stonecutter active "26.1.2-fabric"', 'stonecutter active "1.20.1-forge"', 'active target')
s = replace_once(s,
'constants.match(node.metadata.project.substringAfterLast(\'-\'), "fabric", "neoforge")',
'constants.match(node.metadata.project.substringAfterLast(\'-\'), "fabric", "forge", "neoforge")',
'loader constants')
write('stonecutter.gradle.kts', s)

# ---------------- Gradle build ----------------
s = read('build.gradle')
s = replace_once(s,
'''    id 'net.neoforged.moddev' version '2.0.147' apply false\n''',
'''    id 'net.neoforged.moddev' version '2.0.147' apply false\n    id 'net.neoforged.moddev.legacyforge' version '2.0.147' apply false\n''', 'legacy forge plugin')

s = replace_once(s,
'''        "1.20.1-fabric":   [minecraft: "1.20.1", minecraft_dependency: "1.20.1", fabric: "0.92.2+1.20.1", loader: "0.19.3", cloth_config: "11.1.106", modmenu: "7.2.2", obfuscated: true, java: 17],\n''',
'''        "1.20.1-fabric":   [minecraft: "1.20.1", minecraft_dependency: "1.20.1", fabric: "0.92.2+1.20.1", loader: "0.19.3", cloth_config: "11.1.106", modmenu: "7.2.2", obfuscated: true, java: 17],\n        "1.20.1-forge":    [minecraft: "1.20.1", minecraft_dependency: "1.20.1", forge: "47.4.10", cloth_config: "11.1.106", obfuscated: true, java: 17],\n''', 'forge dependency versions')

s = replace_once(s,
'''def isFabric = loader == 'fabric'\ndef isNeoForge = loader == 'neoforge'\n''',
'''def isFabric = loader == 'fabric'\ndef isForge = loader == 'forge'\ndef isNeoForge = loader == 'neoforge'\n''', 'isForge')

s = replace_once(s,
'''if (isFabric) {\n    apply plugin: 'dev.kikugie.loom-back-compat'\n} else if (isNeoForge) {\n    apply plugin: 'net.neoforged.moddev'\n}\n''',
'''if (isFabric) {\n    apply plugin: 'dev.kikugie.loom-back-compat'\n} else if (isForge) {\n    apply plugin: 'net.neoforged.moddev.legacyforge'\n} else if (isNeoForge) {\n    apply plugin: 'net.neoforged.moddev'\n}\n''', 'apply legacy forge')

s = replace_once(s,
'''    } else if (isNeoForge) {\n        project.ext.neoforge_version = currentVersions.neoforge\n    }\n''',
'''    } else if (isForge) {\n        project.ext.forge_version = currentVersions.forge\n    } else if (isNeoForge) {\n        project.ext.neoforge_version = currentVersions.neoforge\n    }\n''', 'forge project version')

s = replace_once(s,
'''    } else if (isNeoForge) {\n        implementation "me.shedaniel.cloth:cloth-config-neoforge:${project.cloth_config_version}"\n    }\n}\n\nif (isNeoForge) {\n''',
'''    } else if (isForge) {\n        modImplementation "me.shedaniel.cloth:cloth-config-forge:${project.cloth_config_version}"\n        annotationProcessor 'org.spongepowered:mixin:0.8.5:processor'\n        compileOnly(annotationProcessor("io.github.llamalad7:mixinextras-common:0.4.1"))\n        jarJar(implementation("io.github.llamalad7:mixinextras-forge:0.4.1")) {\n            version {\n                strictly '[0.4.1,0.5.0)'\n                prefer '0.4.1'\n            }\n        }\n    } else if (isNeoForge) {\n        implementation "me.shedaniel.cloth:cloth-config-neoforge:${project.cloth_config_version}"\n    }\n}\n\nif (isForge) {\n    legacyForge {\n        version = "${project.minecraft_version}-${project.forge_version}"\n        validateAccessTransformers = true\n        runs {\n            client { client() }\n        }\n        mods {\n            "spatial_gui" {\n                sourceSet sourceSets.main\n            }\n        }\n    }\n    mixin {\n        add sourceSets.main, 'spatial-gui.refmap.json'\n        config 'spatial-gui.mixins.json'\n    }\n}\n\nif (isNeoForge) {\n''', 'forge dependencies and legacyForge block')

s = replace_once(s,
'''    if (isFabric) {\n        exclude "META-INF/neoforge.mods.toml"\n''',
'''    if (isFabric) {\n        exclude "META-INF/neoforge.mods.toml"\n        exclude "META-INF/mods.toml"\n''', 'fabric excludes forge metadata')

s = replace_once(s,
'''    } else if (isNeoForge) {\n        exclude "fabric.mod.json"\n        inputs.property "neoforge_version", project.neoforge_version\n''',
'''    } else if (isForge) {\n        exclude "fabric.mod.json"\n        exclude "META-INF/neoforge.mods.toml"\n        inputs.property "forge_version", project.forge_version\n        inputs.property "minecraft_dependency", project.minecraft_dependency\n        inputs.property "cloth_config_version", project.cloth_config_version\n        filesMatching("META-INF/mods.toml") {\n            expand "version": project.version,\n                    "minecraft_version": project.minecraft_version,\n                    "forge_version": project.forge_version,\n                    "minecraft_dependency": project.minecraft_dependency,\n                    "cloth_config_version": project.cloth_config_version\n        }\n    } else if (isNeoForge) {\n        exclude "fabric.mod.json"\n        exclude "META-INF/mods.toml"\n        inputs.property "neoforge_version", project.neoforge_version\n''', 'forge resource processing')

s = replace_once(s,
'''jar {\n    from("LICENSE") {\n        rename { "${it}_${project.archives_base_name}" }\n    }\n}\n''',
'''jar {\n    from("LICENSE.txt") {\n        rename { "LICENSE_${project.archives_base_name}" }\n    }\n    if (isForge) {\n        manifest.attributes(["MixinConfigs": "spatial-gui.mixins.json"])\n    }\n}\n''', 'jar manifest and license')
write('build.gradle', s)

# ---------------- Forge metadata ----------------
write('src/main/resources/META-INF/mods.toml', """modLoader="javafml"
loaderVersion="[47,)"
license="MIT"

[[mods]]
modId="spatial_gui"
version="${version}"
displayName="Spatial GUI"
logoFile="assets/spatial-gui/icon.png"
displayTest="IGNORE_ALL_VERSION"
description=\'\'\'
A client-side mod that renders inventory & container screens as a 3D plane.
\'\'\'

[[dependencies.spatial_gui]]
modId="forge"
mandatory=true
versionRange="[47.4.10,)"
ordering="NONE"
side="CLIENT"

[[dependencies.spatial_gui]]
modId="minecraft"
mandatory=true
versionRange="[1.20.1,1.21)"
ordering="NONE"
side="CLIENT"

[[dependencies.spatial_gui]]
modId="cloth_config"
mandatory=true
versionRange="[11.1.0,)"
ordering="NONE"
side="CLIENT"
""")

# ---------------- Loader bootstrap ----------------
write('src/main/java/org/tastytrash/spatialGUI/SpatialGUI.java', r'''package org.tastytrash.spatialGUI;

import me.shedaniel.autoconfig.AutoConfig;
import me.shedaniel.autoconfig.serializer.GsonConfigSerializer;
import org.tastytrash.spatialGUI.client.SpatialGUIConfig;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

//? if fabric {
 import net.fabricmc.api.ModInitializer;
//? } else if forge {
/*import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
*///? } else if neoforge {
/*import net.neoforged.fml.common.Mod;
import net.neoforged.fml.ModContainer;
import net.neoforged.neoforge.client.gui.IConfigScreenFactory;
import net.neoforged.bus.api.IEventBus;
*///? }

//? if fabric {
 public class SpatialGUI implements ModInitializer {
//? } else if forge {
/*@Mod(SpatialGUI.MOD_ID)
public class SpatialGUI {
*///? } else if neoforge {
/*@Mod(SpatialGUI.MOD_ID)
public class SpatialGUI {
*///?}
    //? if fabric {
     public static final String MOD_ID = "spatial-gui";
    //? } else {
    /*public static final String MOD_ID = "spatial_gui";
    *///? }
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);
    public static SpatialGUIConfig config;

    //? if fabric {
     @Override
     public void onInitialize() {
         initCommon();
     }
    //?} else if forge {
    /*public SpatialGUI() {
        initCommon();
        new org.tastytrash.spatialGUI.client.SpatialGUIClient(FMLJavaModLoadingContext.get().getModEventBus());
    }
    *///?} else if neoforge {
    /*public SpatialGUI(ModContainer container, IEventBus modBus) {
        initCommon();
        container.registerExtensionPoint(
                IConfigScreenFactory.class,
                (modContainer, parentScreen) -> me.shedaniel.autoconfig.AutoConfigClient.getConfigScreen(SpatialGUIConfig.class, parentScreen).get()
        );
        new org.tastytrash.spatialGUI.client.SpatialGUIClient(modBus);
    }
    *///?}

    private static void initCommon() {
        LOGGER.info("Initializing Spatial GUI");
        AutoConfig.register(SpatialGUIConfig.class, GsonConfigSerializer::new);
        config = AutoConfig.getConfigHolder(SpatialGUIConfig.class).getConfig();
    }
}
''')

write('src/main/java/org/tastytrash/spatialGUI/client/SpatialGUIClient.java', r'''package org.tastytrash.spatialGUI.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.PauseScreen;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.inventory.*;
import org.tastytrash.spatialGUI.compat.VisorCompat;
import org.tastytrash.spatialGUI.render.SpatialGUIRenderer;
import org.tastytrash.spatialGUI.SpatialGUI;
//? if fabric {
 import net.fabricmc.api.ClientModInitializer;
 import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
//? } else if forge {
/*import net.minecraftforge.client.event.ScreenEvent;
import net.minecraftforge.client.event.RegisterKeyMappingsEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.eventbus.api.IEventBus;
*///? } else if neoforge {
/*import net.neoforged.neoforge.client.event.ScreenEvent;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.common.NeoForge;
*///? }

//? if fabric {
 public class SpatialGUIClient implements ClientModInitializer {
//? } else {
/*public class SpatialGUIClient {
*///? }
    private static SpatialGUIRenderer renderer;
    private static boolean effectiveFirstPersonMode = false;
    private static boolean switchedToFirstPersonDueToBlock = false;

    //? if fabric {
    @Override
    public void onInitializeClient() {
        renderer = new SpatialGUIRenderer();
        SpatialGUIKeybinds.register();
        ScreenEvents.BEFORE_INIT.register((clientArg, screen, scaledWidth, scaledHeight) -> {
            if (SpatialGUIClient.shouldHookScreen(screen)) renderer.hookScreen(screen);
        });
    }
    //? } else if forge {
    /*public SpatialGUIClient(IEventBus modBus) {
        renderer = new SpatialGUIRenderer();
        modBus.addListener((RegisterKeyMappingsEvent e) -> SpatialGUIKeybinds.register(e));
        MinecraftForge.EVENT_BUS.addListener(this::onScreenInit);
    }

    private void onScreenInit(ScreenEvent.Init.Pre event) {
        Screen screen = event.getScreen();
        if (SpatialGUIClient.shouldHookScreen(screen)) renderer.hookScreen(screen);
    }
    *///? } else if neoforge {
    /*public SpatialGUIClient(net.neoforged.bus.api.IEventBus modBus) {
        renderer = new SpatialGUIRenderer();
        modBus.addListener((RegisterKeyMappingsEvent e) -> SpatialGUIKeybinds.register(e));
        NeoForge.EVENT_BUS.addListener(this::onScreenInit);
    }

    private void onScreenInit(ScreenEvent.Init.Pre event) {
        var screen = event.getScreen();
        if (SpatialGUIClient.shouldHookScreen(screen)) renderer.hookScreen(screen);
    }
    *///?}

    public static boolean isEnabled() {
        if (VisorCompat.isActive()) return false;
        return SpatialGUI.config.enabled;
    }

    public static boolean shouldHookScreen(Screen screen) {
        if (screen == null) return false;
        String id = screen.getClass().getName();
        if (id.contains("TitleScreen")) return false;
        if (id.contains("ReceivingLevelScreen")) return false;
        if (id.contains("LevelLoadingScreen")) return false;
        if (id.contains("ChatScreen")) return false;

        if (!id.contains("$") && !SpatialGUI.config.seenScreens.contains(id)) SpatialGUI.config.seenScreens.add(id);
        if (SpatialGUI.config.disabledScreens.contains(id)) return false;

        boolean categorized = true;
        boolean toggle;
        if (screen instanceof InventoryScreen || screen instanceof CreativeModeInventoryScreen) {
            toggle = SpatialGUI.config.inventory;
        } else if (screen instanceof AbstractContainerScreen<?>) {
            toggle = SpatialGUI.config.containers;
        } else if (screen instanceof PauseScreen) {
            toggle = SpatialGUI.config.pauseScreen;
        } else {
            categorized = false;
            toggle = false;
        }

        if (categorized) return toggle;
        if (SpatialGUI.config.enabledScreens.contains(id)) return true;
        return SpatialGUI.config.allScreens && Minecraft.getInstance().level != null;
    }

    public static SpatialGUIRenderer renderer() { return renderer; }
    public static boolean getEffectiveFirstPersonMode() { return effectiveFirstPersonMode; }
    public static void setEffectiveFirstPersonMode(boolean value) { effectiveFirstPersonMode = value; }
    public static boolean getSwitchedToFirstPersonDueToBlock() { return switchedToFirstPersonDueToBlock; }
    public static void setSwitchedToFirstPersonDueToBlock(boolean value) { switchedToFirstPersonDueToBlock = value; }
}
''')

write('src/main/java/org/tastytrash/spatialGUI/client/SpatialGUIKeybinds.java', r'''package org.tastytrash.spatialGUI.client;

import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.Screen;

//? if fabric {
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
//?} else if forge {
/*import net.minecraftforge.client.event.RegisterKeyMappingsEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.common.MinecraftForge;
*///?} else if neoforge {
/*import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.common.NeoForge;
*///?}
//? if fabric && >=26.1 {
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
//?} else if fabric {
/*import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
*///?}

public class SpatialGUIKeybinds {
    private static KeyMapping openConfig;
    private static boolean registered = false;

    //? if fabric && >1.21.1 {
    public static final KeyMapping.Category SPATIAL_GUI_CATEGORY =
            KeyMapping.Category.register(net.minecraft.resources.Identifier.fromNamespaceAndPath("spatial-gui", "main_category"));
    //?} else if neoforge && >1.21.1 {
    /*public static final KeyMapping.Category SPATIAL_GUI_CATEGORY =
            new KeyMapping.Category(net.minecraft.resources.Identifier.fromNamespaceAndPath("spatial-gui", "main_category"));
    *///?}

    private static KeyMapping createKey() {
        //? if >1.21.1 {
        return new KeyMapping(
                "key.spatial-gui.open_config",
                InputConstants.UNKNOWN.getType(),
                InputConstants.UNKNOWN.getValue(),
                SPATIAL_GUI_CATEGORY
        );
        //?} else {
        /*return new KeyMapping(
                "key.spatial-gui.open_config",
                InputConstants.UNKNOWN.getType(),
                InputConstants.UNKNOWN.getValue(),
                "key.category.spatial-gui.main_category"
        );
        *///?}
    }

    private static void tick(Minecraft mc) {
        while (openConfig != null && openConfig.consumeClick()) {
            Screen screen = me.shedaniel.autoconfig.AutoConfigClient.getConfigScreen(SpatialGUIConfig.class, null).get();
            //? if >=26.1 {
            mc.setScreenAndShow(screen);
            //?} else {
            /*mc.setScreen(screen);
            *///?}
        }
    }

    //? if fabric && >=26.1.2 {
    public static void register() {
        openConfig = KeyMappingHelper.registerKeyMapping(createKey());
        ClientTickEvents.END_CLIENT_TICK.register(SpatialGUIKeybinds::tick);
    }
    //?} else if fabric {
    /*public static void register() {
        openConfig = KeyBindingHelper.registerKeyBinding(createKey());
        ClientTickEvents.END_CLIENT_TICK.register(SpatialGUIKeybinds::tick);
    }
    *///?} else if forge {
    /*public static void register(RegisterKeyMappingsEvent event) {
        if (registered) return;
        registered = true;
        openConfig = createKey();
        event.register(openConfig);
        MinecraftForge.EVENT_BUS.addListener(SpatialGUIKeybinds::onClientTick);
    }

    private static void onClientTick(TickEvent.ClientTickEvent event) {
        if (event.phase == TickEvent.Phase.END) tick(Minecraft.getInstance());
    }
    *///?} else if neoforge {
    /*public static void register(RegisterKeyMappingsEvent event) {
        if (registered) return;
        registered = true;
        //? if >1.21.1 {
        event.registerCategory(SPATIAL_GUI_CATEGORY);
        //?}
        openConfig = createKey();
        event.register(openConfig);
        NeoForge.EVENT_BUS.addListener((ClientTickEvent.Post e) -> tick(Minecraft.getInstance()));
    }
    *///?}
}
''')

write('src/main/java/org/tastytrash/spatialGUI/compat/VulkanModCompat.java', r'''//? if fabric {
package org.tastytrash.spatialGUI.compat;

import net.fabricmc.loader.api.FabricLoader;

public final class VulkanModCompat {
    private static Boolean isVulkanModLoaded = null;
    public static boolean isVulkanModLoaded() {
        if (isVulkanModLoaded != null) return isVulkanModLoaded;
        isVulkanModLoaded = FabricLoader.getInstance().isModLoaded("vulkanmod");
        return isVulkanModLoaded;
    }
}
//?} else {
/*package org.tastytrash.spatialGUI.compat;

public final class VulkanModCompat {
    public static boolean isVulkanModLoaded() { return false; }
}
*///?}
''')

# ---------------- Renderer event hooks ----------------
s = read('src/main/java/org/tastytrash/spatialGUI/render/SpatialGUIRenderer.java')
s = replace_once(s,
'''//? if fabric {\n import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;\n//? } else if neoforge {\n/*import net.neoforged.neoforge.client.event.ScreenEvent;\nimport net.neoforged.neoforge.common.NeoForge;\n*///? }\n''',
'''//? if fabric {\n import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;\n//? } else if forge {\n/*import net.minecraftforge.client.event.ScreenEvent;\nimport net.minecraftforge.common.MinecraftForge;\n*///? } else if neoforge {\n/*import net.neoforged.neoforge.client.event.ScreenEvent;\nimport net.neoforged.neoforge.common.NeoForge;\n*///? }\n''', 'renderer imports')

s = replace_once(s,
'''        //? if neoforge {\n        /*NeoForge.EVENT_BUS.addListener(this::onScreenRenderPre);\n        NeoForge.EVENT_BUS.addListener(this::onScreenClosing);\n        *///? }\n''',
'''        //? if forge {\n        /*MinecraftForge.EVENT_BUS.addListener(this::onScreenRenderPre);\n        MinecraftForge.EVENT_BUS.addListener(this::onScreenClosing);\n        *///? } else if neoforge {\n        /*NeoForge.EVENT_BUS.addListener(this::onScreenRenderPre);\n        NeoForge.EVENT_BUS.addListener(this::onScreenClosing);\n        *///? }\n''', 'renderer constructor events')

old_methods = '''    //? if neoforge {\n    /*private void onScreenRenderPre(ScreenEvent.Render.Pre event) {\n        if (event.getScreen() == hookedScreen) {\n            event.setCanceled(true);\n            SpatialGUIRenderer.skipWindowOverride = false;\n            screenExtractor.extractIsolatedScreen(hookedScreen, event.getPartialTick(), inventoryRenderer.getQuadBasis(), inventoryRenderer.getCylinderBasis(), targetManager);\n            SpatialGUIRenderer.skipWindowOverride = true;\n        }\n    }\n\n    private void onScreenClosing(ScreenEvent.Closing event) {\n        if (event.getScreen() == hookedScreen) {\n            onScreenRemoved();\n        }\n    }\n    *///? }\n'''
new_methods = '''    //? if forge {\n    /*private void onScreenRenderPre(ScreenEvent.Render.Pre event) {\n        if (event.getScreen() == hookedScreen) {\n            event.setCanceled(true);\n            SpatialGUIRenderer.skipWindowOverride = false;\n            screenExtractor.extractIsolatedScreen(hookedScreen, event.getPartialTick(), inventoryRenderer.getQuadBasis(), inventoryRenderer.getCylinderBasis(), targetManager);\n            SpatialGUIRenderer.skipWindowOverride = true;\n        }\n    }\n\n    private void onScreenClosing(ScreenEvent.Closing event) {\n        if (event.getScreen() == hookedScreen) onScreenRemoved();\n    }\n    *///? } else if neoforge {\n    /*private void onScreenRenderPre(ScreenEvent.Render.Pre event) {\n        if (event.getScreen() == hookedScreen) {\n            event.setCanceled(true);\n            SpatialGUIRenderer.skipWindowOverride = false;\n            screenExtractor.extractIsolatedScreen(hookedScreen, event.getPartialTick(), inventoryRenderer.getQuadBasis(), inventoryRenderer.getCylinderBasis(), targetManager);\n            SpatialGUIRenderer.skipWindowOverride = true;\n        }\n    }\n\n    private void onScreenClosing(ScreenEvent.Closing event) {\n        if (event.getScreen() == hookedScreen) onScreenRemoved();\n    }\n    *///? }\n'''
s = replace_once(s, old_methods, new_methods, 'renderer screen event methods')
write('src/main/java/org/tastytrash/spatialGUI/render/SpatialGUIRenderer.java', s)

# ---------------- Forge GameRenderer screen hook ----------------
s = read('src/main/java/org/tastytrash/spatialGUI/mixin/render/GameRendererMixin.java')
neo_block = '''    //?} else {\n    /^@Redirect(method = "render", at = @At(\n            value = "INVOKE",\n            target = "Lnet/neoforged/neoforge/client/ClientHooks;drawScreen(Lnet/minecraft/client/gui/screens/Screen;Lnet/minecraft/client/gui/GuiGraphics;IIF)V"\n    ))\n    private void spatialGUI$redirectScreenExtraction(Screen screen, GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {\n        var renderer = SpatialGUIClient.renderer();\n        if (SpatialGUIClient.isEnabled() && SpatialGUIClient.shouldHookScreen(screen) && screen == renderer.getHookedScreen()) {\n            SpatialGUIRenderer.skipWindowOverride = false;\n            renderer.extractIsolatedScreen(screen, partialTick);\n            SpatialGUIRenderer.skipWindowOverride = true;\n            renderer.renderInWorldPost();\n        } else {\n            net.neoforged.neoforge.client.ClientHooks.drawScreen(screen, graphics, mouseX, mouseY, partialTick);\n        }\n    }\n    ^///?}\n'''
forge_neoblock = '''    //?} else if forge {\n    /^@Redirect(method = "render", at = @At(\n            value = "INVOKE",\n            target = "Lnet/minecraftforge/client/ForgeHooksClient;drawScreen(Lnet/minecraft/client/gui/screens/Screen;Lnet/minecraft/client/gui/GuiGraphics;IIF)V"\n    ))\n    private void spatialGUI$redirectScreenExtraction(Screen screen, GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {\n        var renderer = SpatialGUIClient.renderer();\n        if (SpatialGUIClient.isEnabled() && SpatialGUIClient.shouldHookScreen(screen) && screen == renderer.getHookedScreen()) {\n            SpatialGUIRenderer.skipWindowOverride = false;\n            renderer.extractIsolatedScreen(screen, partialTick);\n            SpatialGUIRenderer.skipWindowOverride = true;\n            renderer.renderInWorldPost();\n        } else {\n            net.minecraftforge.client.ForgeHooksClient.drawScreen(screen, graphics, mouseX, mouseY, partialTick);\n        }\n    }\n    ^///?} else if neoforge {\n    /^@Redirect(method = "render", at = @At(\n            value = "INVOKE",\n            target = "Lnet/neoforged/neoforge/client/ClientHooks;drawScreen(Lnet/minecraft/client/gui/screens/Screen;Lnet/minecraft/client/gui/GuiGraphics;IIF)V"\n    ))\n    private void spatialGUI$redirectScreenExtraction(Screen screen, GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {\n        var renderer = SpatialGUIClient.renderer();\n        if (SpatialGUIClient.isEnabled() && SpatialGUIClient.shouldHookScreen(screen) && screen == renderer.getHookedScreen()) {\n            SpatialGUIRenderer.skipWindowOverride = false;\n            renderer.extractIsolatedScreen(screen, partialTick);\n            SpatialGUIRenderer.skipWindowOverride = true;\n            renderer.renderInWorldPost();\n        } else {\n            net.neoforged.neoforge.client.ClientHooks.drawScreen(screen, graphics, mouseX, mouseY, partialTick);\n        }\n    }\n    ^///?}\n'''
if neo_block not in s:
    raise RuntimeError('Expected old-version NeoForge GameRenderer redirect not found')
s = s.replace(neo_block, forge_neoblock, 1)
write('src/main/java/org/tastytrash/spatialGUI/mixin/render/GameRendererMixin.java', s)

print('\nForge 1.20.1 port patch applied successfully.')
