# Third-party materials and restoring omitted assets

Prepared for the code archive on 18 September 2026. This archive preserves the project source and configuration. It does not grant rights to external software or artwork. The original development project has not been changed by this packaging step.

## Archive contents and omissions

`OMITTED_ASSETS.csv` lists 314 omitted content files (32,567,110 bytes): 159 artwork files and 155 TextMesh Pro dependency files. Each row gives the original project-relative path, SHA-256 hash, byte size, Unity GUID, paired metadata path and hash, and restoration guidance. The CSV contains identifiers and hashes, not the omitted file contents. All 314 paired `.meta` files are retained to preserve import settings and references.

The following project material remains in the archive: the game scripts, scenes, prefabs, animation and controller configuration, scenario definitions, tile assets, project settings and package declarations. No original game scripts were removed by this asset-omission step. Imported TextMesh Pro example scripts are external examples, not the project's own scripts.

| Material | Treatment | Attribution and evidence |
| --- | --- | --- |
| Artwork under `Assets/RPG`, `Assets/Sprites` and `Assets/UI` | 159 PNG, PSD and Aseprite files omitted; import metadata and the surrounding game configuration retained | The dissertation credits Tiny Swords by Pixel Frog. The folder also includes an icon collection whose author has not been established. The retained records do not prove the source and licence version of every individual image. |
| TextMesh Pro resources and examples | 155 files omitted, including fonts, generated font atlases, imported examples and shaders | External Unity/TextMesh Pro resources. Compared with the installed Unity resource packages before omission. Project-specific or changed materials and `TMP Settings.asset` were retained. |
| Existing font notices | Seven notice files retained in their original paths and copied to `Docs/ThirdPartyLicenses` | Liberation Sans, Anton, Bangers, Oswald, Roboto and Unity notices; the two Roboto notice files describe Apache License 2.0. |
| Unity packages | Dependency declarations retained in `Packages`; package cache and editor installation are external dependencies | Unity Technologies and the relevant package authors. |
| Python packages and sentence encoder | Dependency declarations and recorded analysis information retained; installed environments and model weights are external dependencies | OpenAI Python SDK, Pydantic, Sentence Transformers and the packages named by the project's dependency files. The encoder is `sentence-transformers/all-mpnet-base-v2`. |

## Tiny Swords and other artwork

The official [Tiny Swords page by Pixel Frog](https://pixelfrog-assets.itch.io/tiny-swords), checked on 18 September 2026, allows personal and commercial use and modification, but prohibits redistribution, resale or repackaging of its assets. The page does not state an academic-submission exception. Purchasing an asset pack does not by itself establish permission to include its raw source files in another archive.

That page also lists an older download labelled CC0. No retained per-file record establishes that all artwork in this project came from that old download, so the older label has not been applied to the present files. No claim is made about which licence applied at purchase. The omission avoids making an unsupported redistribution claim.

`Assets/UI/Icon` contains a separate collection of fire, water, wind, heart and other icons. A matching local download is named `simple_rpg_icons.zip`, but contains no licence or author notice. Its author and permission to redistribute are unresolved. These files are omitted and are not attributed to Pixel Frog. The `Assets/RPG` folder also lacks a local per-file attribution record; the dissertation's overall Tiny Swords credit is not proof of each file's origin.

## TextMesh Pro, fonts and retained materials

The local Unity uGUI package contains `TMP Essential Resources.unitypackage` and `TMP Examples & Extras.unitypackage`. Before packaging, 158 of the 170 original TextMesh Pro content files matched these installed package payloads exactly; 11 differed and one material was absent from them. A difference may result from an editor conversion or a project edit, so it is not treated as proof of original authorship.

The archive retains `TMP Settings.asset`, the project-specific `Bangers SDF - Inventory.mat`, and six other material files that differ from the installed package. These materials refer to omitted font or shader dependencies. No font atlas has been substituted or regenerated. Some omitted generated font assets differ from their package defaults, so importing fresh defaults alone does not guarantee exact visual reproduction.

The original font notices identify SIL Open Font License 1.1 for Liberation Sans, Anton, Bangers, Oswald and Unity, and Apache License 2.0 for Roboto. Copies are retained under `Docs/ThirdPartyLicenses`. A separate notice for `Electronic Highway Sign.TTF` was not found in the project, so its terms are not inferred from the other fonts. All font binaries and atlases have been omitted consistently; omission does not imply that the fonts with permissive notices prohibit redistribution.

The installed uGUI package notice is copied to `Docs/ThirdPartyLicenses/Unity-uGUI-LICENSE.md`. It identifies the Unity Companion License for Unity-dependent projects. Retained package-derived configuration remains external material and is not claimed as original project code. Primary licence sources are the [Unity Companion License](https://unity.com/legal/licenses/unity-companion-license), [SIL Open Font License](https://openfontlicense.org/) and [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0). The actual font copyright notices retained with the project should be read with their respective licences.

## Restoring a local working copy

1. Keep the submitted archive intact. Extract a separate working copy for restoration, and restore the missing files **before opening that copy in Unity**. Unity may remove `.meta` files whose source files are missing during import.
2. The project owner can copy their own lawfully obtained original content files into the exact relative paths listed in `OMITTED_ASSETS.csv`. Preserve the paired `.meta` files already in the archive. Copying a different release with a similar filename may not match sprite slicing, animation references or font configuration.
3. Compare each restored file's SHA-256 hash with the CSV to check exact restoration. Matching the retained GUIDs is also important: Unity scenes and prefabs refer to GUIDs, not merely filenames. Do not replace or regenerate the metadata as a shortcut. If Unity already removed it, restore the metadata from a fresh archive extraction.
4. Anyone else restoring the artwork needs their own lawful access to the required versions, or permission from the rights holder. The archive is not a source of the omitted licensed artwork. New downloads may require manual remapping if their layout differs from the original files.
5. For baseline TextMesh Pro dependencies, Unity documents **Window > TextMeshPro > Import TMP Essential Resources** and **Import TMP Examples & Extras**. Import only the missing resources and preserve the retained project settings and changed materials. The project uses Bangers resources from Examples & Extras, so the essential resources alone do not restore its original font appearance. Exact reproduction of edited font assets requires the owner's original matching files. See the [official TextMesh Pro import instructions](https://docs.unity3d.com/Packages/com.unity.textmeshpro@4.0/manual/index.html), checked on 18 September 2026.
6. Use the Unity version and package declarations in the project and follow the main README for backend setup. After restoration, inspect references and test both game scenes before assuming the original appearance and behaviour have been reproduced.

Without these dependencies, this submission is a source-and-evidence archive, not a complete playable distribution. Missing sprites, fonts and shaders are expected, and a fresh Unity build has not been validated from this stripped archive. The supplied backend and analysis work can be inspected separately from the omitted game artwork. The module's code-archive instructions permit an archive that cannot be installed or executed and require external libraries to be acknowledged; no exemption from external licence terms is assumed.

## Other external dependencies

`Packages/manifest.json` and `Packages/packages-lock.json` identify Unity packages used by the project. `Backend/requirements.txt` and `Backend/requirements-semantic.txt` identify Python dependencies; the saved analysis metadata records the analysis environment. These files, rather than this short notice, provide the version information. Relevant primary project pages include [Unity documentation](https://docs.unity3d.com/), [OpenAI Python SDK](https://github.com/openai/openai-python), [Pydantic](https://docs.pydantic.dev/), [Sentence Transformers](https://www.sbert.net/) and the [all-mpnet-base-v2 model card](https://huggingface.co/sentence-transformers/all-mpnet-base-v2). Each dependency remains subject to its own terms. No blanket licence is applied to all dependencies by this archive.
