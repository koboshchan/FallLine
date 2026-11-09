# Fall Line

A work-in-progress skiing game in Unreal Engine 5.8.4, built around a Chaos rigid-body skier and real terrain near Verbier.

A/D steer, W pushes, S brakes, Space jumps, and R resets. Mouse X rotates the chase camera. Gamepad steering, triggers, jump and reset are also mapped.

## Run it

You need Windows, Unreal Engine **5.8.4**, Visual Studio 2022 with the C++ game-development tools and Windows SDK, Python 3, and Git LFS.

Clone with Git LFS enabled. The current launcher and development scripts expect the project at `D:/FallLine` and the engine at `D:/EpicGames/UE_5.8`. Adjust those paths if your setup differs.

Restore the excluded Epic mannequin assets from your own installed engine with `python Scripts/import-skier-template.py`. Then run `powershell -ExecutionPolicy Bypass -File Scripts/Build.ps1`, open **Open-FallLine.cmd**, and press Play. The startup map is `/Game/Maps/TestSlope`.

This is a development project, not a packaged release. Physics smoke tests have passed locally; snow shading, forest placement and the skiing feel are still being worked on. Public-clone startup has not yet been tested.

## Project layout

`Source/` holds gameplay C++, `Content/` holds Unreal assets, and `Config/` holds engine settings. `Scripts/` contains build, import, capture and verification tools. `SourceAssets/` keeps small provenance records and the processed heightmap; raw downloads and local outputs are excluded. Further notes live in [docs](docs/).

Terrain derived from swissALTI3D, **©swisstopo**. Environment assets come from Poly Haven under CC0. See [asset sources and restoration](docs/Assets.md) before redistributing assets.

Project-authored work is [MIT licensed](LICENSE); third-party assets keep their own terms, including Poly Haven CC0 and swissALTI3D attribution. See [asset licensing](docs/Assets.md).
