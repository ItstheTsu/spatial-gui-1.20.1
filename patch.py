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
