Mature alpine fir source and derivative

Poly Haven fir_tree_01 by Rico Cilliers and Rob Tuytel.
Source https://polyhaven.com/a/fir_tree_01
License https://polyhaven.com/license , CC0 confirmed on live asset page.
Source metadata https://api.polyhaven.com/files/fir_tree_01
Source manifest records exact URLs, original byte sizes and MD5.
download-result.json records verified source SHA256 for every downloaded file.
single-fir-manifest.json records derivative SHA256, bounds and round-trip check.

ExportMatureFir.py selects original tree a, places its trunk origin at XY zero and bottom at Z zero, applies Blender decimation, exports FBX. Actual output 1199194 polygons, not the requested 650000 target because collapse preservation/topology retains additional faces. Preserve alpha twig geometry and material assignments. Original source is unmodified. CheckMatureFir.py imports the derivative separately and verifies one mesh, real 18.9254m tree height and ground-aligned bounds. Unreal importer maps twig masked two-sided, trunk_a unique bark and other wood bark. Texture units convert through FBX centimetres, then placement scales by measured UE bounds to 11–22.5m.

Fab alternatives researched live without acquiring anything

Megaplants Baltic Pine https://www.fab.com/listings/a2b04e81-5075-479f-a9d2-4940022f330a
Rock Cliff https://www.fab.com/listings/22762313-071f-4017-a721-b29c5a2f1a87

Both live public pages display Free and zero USD offer, but their extracted license terms are '-' and account-specific entitlement was not verified. Neither was acquired or imported. No charged acquisition is authorized. Safe implemented fallback is the CC0 Poly Haven fir, existing CC0 snow_02 and boulder_01.

If a human chooses Fab instead, open the exact listing, sign into the intended Epic account, select Add to My Library and inspect the actual offered license and zero total before accepting. Stop for any nonzero price. In Epic Games Launcher open Unreal Engine, Library, refresh Fab Library, find the acquired product and choose Add to Project only if that product supports Unreal Engine assets. Texture-set/glTF-only listings need direct Download/import instead, not a guaranteed Add to Project action. No account-specific launcher UI was inspected here.

Source changes were Python-compiled and an isolated stubbed sampler-only forest test passed. This is not an Unreal import, shader compilation, runtime HISM, actual DEM population or visual acceptance result. Parent owns all UE generation and screenshots. No ZIP deliverable.
