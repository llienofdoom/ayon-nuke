# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Nuke addon for AYON** - an addon that provides Nuke integration with AYON (All You Own Now), a robust pipeline management system for animation and VFX. The addon enables:
- Publishing assets (models, renders, etc.) to AYON server
- Loading published assets into Nuke scenes
- Workfile building and template management
- Asset validation and error reporting
- Integration with AYON project hierarchy

Part of the broader Luma Studios AYON deployment (monorepo at `../../../_DEV/`). Addons are independently versioned and can be developed/tested in isolation.

## Architecture

The addon follows a **client-server architecture**:

- **Client (`client/ayon_nuke/`)**: Python code that runs within Nuke DCC application
  - `api/`: API modules for interacting with Nuke
  - `plugins/`: Contains create, publish, load, and inventory plugins
  - `hooks/`: Nuke-specific hooks (startup, application initialization)
  - `startup/`: Startup scripts executed when Nuke launches with AYON
  - `vendor/`: Vendored third-party dependencies (e.g., protobuf)

- **Server (`server/`)**: Python code running on AYON server
  - `settings/`: Configuration schemas for all settings exposed in AYON UI
    - `main.py`: Root settings model combining all subsettings
    - `create_plugins.py`, `publish_plugins.py`, `loader_plugins.py`: Plugin configurations
    - `imageio.py`, `dirmap.py`, `gizmo.py`, `scriptsmenu.py`: Feature-specific settings
    - `conversion.py`: Settings migration/conversion logic between versions

- **Package Building (`create_package.py`)**: Script that packages client and server code into a distributable addon package with structure `package/{addon_name}/{addon_version}/`

## Common Development Commands

### Code Quality & Linting

```bash
# Run ruff linting on the entire codebase
ruff check .

# Run ruff with automatic fixes
ruff check . --fix

# Format code using ruff formatter
ruff format .

# Check formatting without making changes
ruff format . --check
```

The project uses **ruff** for linting with configuration in `ruff.toml` (79 character line length limit, Black-compatible formatting). GitHub CI enforces linting on pull requests.

### Building & Packaging

```bash
# Create the addon package for distribution
python create_package.py

# Create package in a specific output directory
python create_package.py --output_dir /path/to/output
```

This generates the package structure `package/nuke/{version}/` that can be deployed to AYON servers.

**Deploying to Local AYON Server** (from parent `_DEV` directory):
```bash
# Build addon package
python create_package.py --output_dir ../../../_DEV/addons/

# Restart server to reload addons
cd ../../../_DEV
docker compose restart server
```

**Testing**:
1. Start AYON server and Nuke
2. Create a test project in AYON
3. Launch Nuke with AYON integration
4. Test publish/load workflows
5. Validate settings are applied from server

### Documentation

```bash
# Install documentation dependencies
pip install -r mkdocs_requirements.txt

# Serve documentation locally (auto-reloads on changes)
mkdocs serve

# Build documentation for deployment
mkdocs build
```

MkDocs configuration uses Material theme with API auto-documentation from docstrings. GitHub Actions automatically deploys docs on version tags.

## Key Files & Patterns

### Settings Configuration
All server-side settings are defined in `server/settings/` as Pydantic models. Each feature area (publish, loader, imageio, etc.) has its own settings file with validation. The `__init__.py` combines them into the main `NukeSettings` model.

### Plugin Structure
- Client plugins are in `client/ayon_nuke/plugins/{plugin_type}/`
- Each plugin typically inherits from AYON base plugin classes (CreatedInstances, PublishInstancePlugin, etc.)
- Plugins are auto-discovered by AYON based on directory structure

### Environment Setup
The addon modifies Nuke's environment via `addon.py:NukeAddon.add_implementation_envs()`:
- Adds addon paths to `NUKE_PATH`
- Injects vendor libraries into `PYTHONPATH`
- Removes conflicting Qt/Tk settings
- Sets logging defaults

### Workfile Extensions
The addon registers `.nk` as the Nuke workfile extension format.

## Version & Dependencies

- **Minimum Python**: 3.9 (see `create_package.py`)
- **Minimum AYON Server**: 1.1.2 (see `package.py`)
- **Required Core Addon**: 1.1.0+
- **Package Manager**: Uses `uv` with `uv.lock` for reproducible dependency management
- Documentation dependencies listed in `mkdocs_requirements.txt`

### Versioning (Luma Studios)

This addon follows **Luma Studios Semantic Versioning** for forked ynput addons:

**Format**: `{upstream_version}+ls.{luma_major}.{luma_minor}.{luma_patch}`

**Example**: `0.4.8+ls.0.1.0`
- `0.4.8` - Base ynput version (stays in sync with upstream)
- `+ls.0.1.0` - Luma Studios version
  - `ls` = Luma Studios identifier
  - First number: major (architectural/breaking Luma change)
  - Second number: minor (new features, upstream sync)
  - Third number: patch (bug fixes)

**Version Update Locations** (update ALL when versioning):
1. `package.py` - Main version declaration
2. `client/ayon_nuke/version.py` - Client version (`__init__.py` re-exports from here)

**Bump Guidelines**:
- Bug fix: `0.4.8+ls.0.1.0` → `0.4.8+ls.0.1.1`
- New feature: `0.4.8+ls.0.1.1` → `0.4.8+ls.0.2.0`
- Major Luma change: `0.4.8+ls.0.2.0` → `0.4.8+ls.1.0.0`
- Upstream sync: `0.4.8+ls.0.1.0` → `0.4.9+ls.0.2.0` (new base, increment minor, reset patch)

## Development Workflow

1. **Make changes** to client code in `client/ayon_nuke/` or server settings in `server/settings/`
2. **Run linting**: `ruff check . --fix` to catch issues early
3. **Update version** in `package.py` if needed (format: X.Y.Z+dev for development)
4. **Test locally** by running create_package.py and verifying package structure
5. **Build documentation** with `mkdocs build` if adding/modifying features
6. **Push and create PR** against `develop` branch - GitHub CI will lint automatically
7. **Settings migrations**: If changing settings structure, update `server/settings/conversion.py` with migration logic

## Important Implementation Details

### Settings Versioning
When modifying settings schemas, implement conversion logic in `server/settings/conversion.py` to maintain backward compatibility with existing server configurations.

### Nuke Path Management
The addon carefully manages `NUKE_PATH` by preserving existing paths and inserting addon paths at the beginning. This ensures proper plugin discovery while respecting user configurations.

### Qt/Tk Environment
The addon explicitly removes `QT_AUTO_SCREEN_SCALE_FACTOR`, `TK_LIBRARY`, and `TCL_LIBRARY` to prevent conflicts with Nuke's own Qt/Tk handling.

## Testing Considerations

No automated test framework is currently configured in the repo. Manual testing in Nuke is the primary validation method. When making changes:
- Test with actual Nuke workfiles
- Verify plugin discovery and execution
- Check publish/load workflows end-to-end
- Validate settings are properly applied from server

## Recent Implementation Notes

### Audio Support in Review MOV (extract_review_intermediates.py)

The review MOV generation now includes audio file support:
- Searches for AudioRead nodes in the composition (uses first found)
- Extracts the audio file path from the AudioRead node
- Attaches the audio to the review MOV via the `mov64_audiofile` knob
- Wrapped in try-except to avoid breaking review MOV generation if audio is unavailable or knob doesn't exist
- Logs success or warnings for debugging

**Location**: `client/ayon_nuke/api/plugin.py:ExporterReviewMov.generate_mov()` (lines 1286-1299, 1567-1571)

### Nuke Version Compatibility for Viewer Colorspace (lib.py)

Fixed viewer colorspace setting to work across Nuke versions:
- **Nuke 13**: Uses `monitorOutLUT` knob for monitor output settings
- **Nuke 14+**: Uses `monitorOutOutputTransform` knob
- Code now dynamically selects the correct knob using `nuke.NUKE_VERSION_MAJOR`
- All knob settings wrapped in try-except blocks for robustness

**Location**: `client/ayon_nuke/api/lib.py:set_viewers_colorspace()` (lines 1507-1576)

**Key Changes**:
- Line 1518: Version-aware knob selection
- Line 1523: Filter knobs uses dynamic variable
- Line 1569: Setting uses dynamic knob name with error handling

## Commit Conventions

Follow **semantic commit format**:

```
<type>(<scope>): <summary>
```

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `perf`, `chore`

**Scopes** (examples): `create`, `publish`, `load`, `imageio`, `gizmo`, `workfile`, `settings`

**Examples**:
- `fix(publish): correct gizmo path argument`
- `feat(load): add support for proxy representations`
- `docs(imageio): update configuration examples`
- `refactor(settings): simplify color space handling`

## Branch Convention

- `develop`: Main development branch (CI/CD enabled)
- Feature branches: Created from develop for new features/fixes
- Version releases: Tagged on develop with format matching `package.py` (e.g., `0.3.0-ls.0.1`)

