#!/usr/bin/env bash
# install-premortem.sh
#
# Installs the premortem-code skill (Phases 1, 2, 3) into the user's
# Claude Code skills directory.
#
# Usage:
#   ./install-premortem.sh [--scope=personal|project] [--source=<dir>] [--prune]
#
# Defaults:
#   --scope=personal   installs to ~/.claude/skills/premortem-code/
#   --source=$PWD      assumes script is run from a dir containing
#                      fase1/, fase2/, fase3/ subdirectories with the
#                      delivered skill files
#   --prune            wipe target assets/ and scripts/ before copying
#                      (removes stale/renamed files from a previous install)
#
# Exit codes:
#   0: success
#   1: usage error
#   2: source files not found
#   3: target directory issue

set -euo pipefail
# Unmatched globs expand to nothing (not a literal string), so an empty
# assets/ dir can never abort the install via `cp '<dir>/*.md'`.
shopt -s nullglob

SCOPE="personal"
SOURCE_DIR="$PWD"
SKILL_NAME="premortem-code"
PRUNE=0

usage() {
  # Print the header comment block (lines 2..first blank), stripping the
  # "# " prefix. -E keeps this portable across GNU and BSD/macOS sed.
  sed -n '2,/^$/p' "$0" | sed -E 's/^#[[:space:]]?//'
}

# Parse args. A while/shift loop is used (not `for arg in "$@"`) so that
# shift actually consumes positional parameters as intended.
while [ $# -gt 0 ]; do
  case "$1" in
    --scope=*)
      SCOPE="${1#*=}"
      ;;
    --source=*)
      SOURCE_DIR="${1#*=}"
      ;;
    --prune)
      PRUNE=1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      echo "Run with --help for usage." >&2
      exit 1
      ;;
  esac
  shift
done

# Determine target directory based on scope
case "$SCOPE" in
  personal)
    TARGET_DIR="$HOME/.claude/skills/$SKILL_NAME"
    ;;
  project)
    # `.git` is a directory in a normal clone but a *file* in linked
    # worktrees and submodules, so test for a work tree, not for `-d .git`.
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      echo "Error: --scope=project requires running inside a git work tree." >&2
      exit 3
    fi
    REPO_ROOT="$(git rev-parse --show-toplevel)"
    TARGET_DIR="$REPO_ROOT/.claude/skills/$SKILL_NAME"
    ;;
  *)
    echo "Error: scope must be 'personal' or 'project', got '$SCOPE'" >&2
    exit 1
    ;;
esac

echo "==> Installing premortem-code skill"
echo "    Source: $SOURCE_DIR"
echo "    Target: $TARGET_DIR"
echo "    Scope:  $SCOPE"
echo "    Prune:  $([ "$PRUNE" -eq 1 ] && echo yes || echo no)"
echo

# Verify source directory structure
if [ ! -d "$SOURCE_DIR" ]; then
  echo "Error: source directory does not exist: $SOURCE_DIR" >&2
  exit 2
fi

# Look for SKILL.md in expected locations
SKILL_MD=""
PHASE1_DIR=""
for candidate in \
  "$SOURCE_DIR/premortem-code-fase1/SKILL.md" \
  "$SOURCE_DIR/fase1/SKILL.md" \
  "$SOURCE_DIR/SKILL.md"; do
  if [ -f "$candidate" ]; then
    SKILL_MD="$candidate"
    PHASE1_DIR="$(dirname "$candidate")"
    break
  fi
done

if [ -z "$SKILL_MD" ]; then
  echo "Error: SKILL.md not found. Expected one of:" >&2
  echo "  $SOURCE_DIR/premortem-code-fase1/SKILL.md" >&2
  echo "  $SOURCE_DIR/fase1/SKILL.md" >&2
  echo "  $SOURCE_DIR/SKILL.md" >&2
  exit 2
fi

# Find Phase 2 directory
PHASE2_DIR=""
for candidate in \
  "$SOURCE_DIR/premortem-code-fase2" \
  "$SOURCE_DIR/fase2"; do
  if [ -d "$candidate/assets" ]; then
    PHASE2_DIR="$candidate"
    break
  fi
done

# Find Phase 3 directory
PHASE3_DIR=""
for candidate in \
  "$SOURCE_DIR/premortem-code-fase3" \
  "$SOURCE_DIR/fase3"; do
  if [ -d "$candidate/assets" ]; then
    PHASE3_DIR="$candidate"
    break
  fi
done

# Create target structure
echo "==> Creating target directories"
mkdir -p "$TARGET_DIR/assets" "$TARGET_DIR/scripts"

# Optional prune so renamed/removed addenda don't linger from a prior install.
if [ "$PRUNE" -eq 1 ]; then
  echo "==> Pruning existing assets/ and scripts/"
  prune_assets=( "$TARGET_DIR/assets"/* )
  prune_scripts=( "$TARGET_DIR/scripts"/* )
  (( ${#prune_assets[@]} )) && rm -f "${prune_assets[@]}"
  (( ${#prune_scripts[@]} )) && rm -f "${prune_scripts[@]}"
fi

# Copy Phase 1 (core). SKILL.md is a single, required file.
echo "==> Copying Phase 1 (core)"
cp "$SKILL_MD" "$TARGET_DIR/SKILL.md"
p1_assets=( "$PHASE1_DIR/assets"/*.md )
if (( ${#p1_assets[@]} )); then
  cp "${p1_assets[@]}" "$TARGET_DIR/assets/"
fi
echo "    Installed SKILL.md + ${#p1_assets[@]} core asset(s)"

# Copy Phase 2 (stack addenda)
if [ -n "$PHASE2_DIR" ]; then
  echo "==> Copying Phase 2 (stack addenda)"
  p2_assets=( "$PHASE2_DIR/assets"/stack-*.md )
  if (( ${#p2_assets[@]} )); then
    cp "${p2_assets[@]}" "$TARGET_DIR/assets/"
  fi
  echo "    Installed ${#p2_assets[@]} stack addendum file(s)"
else
  echo "==> Phase 2 not found, skipping (skill will work but with reduced coverage)"
fi

# Copy Phase 3 (refinements: extra addenda + SARIF exporter)
if [ -n "$PHASE3_DIR" ]; then
  echo "==> Copying Phase 3 (refinements)"
  p3_assets=( "$PHASE3_DIR/assets"/*.md )
  p3_scripts=( "$PHASE3_DIR/scripts"/*.py )
  if (( ${#p3_assets[@]} )); then
    cp "${p3_assets[@]}" "$TARGET_DIR/assets/"
  fi
  if (( ${#p3_scripts[@]} )); then
    cp "${p3_scripts[@]}" "$TARGET_DIR/scripts/"
    installed_scripts=( "$TARGET_DIR/scripts"/*.py )
    (( ${#installed_scripts[@]} )) && chmod +x "${installed_scripts[@]}"
  fi
  echo "    Installed ${#p3_assets[@]} refinement addenda + ${#p3_scripts[@]} script(s)"
else
  # Flat-layout fallback (R1-PRC001): a single-dir skill repo keeps scripts at
  # $SOURCE_DIR/scripts/ rather than in a fase3/ dir. Copy those too.
  flat_scripts=( "$SOURCE_DIR/scripts"/*.py )
  if (( ${#flat_scripts[@]} )); then
    echo "==> Phase 3 dir not found; using flat \$SOURCE_DIR/scripts fallback"
    cp "${flat_scripts[@]}" "$TARGET_DIR/scripts/"
    installed_scripts=( "$TARGET_DIR/scripts"/*.py )
    (( ${#installed_scripts[@]} )) && chmod +x "${installed_scripts[@]}"
    echo "    Installed ${#flat_scripts[@]} script(s) from flat layout"
  else
    echo "==> Phase 3 not found and no flat scripts/, skipping (no SARIF export)"
  fi
fi

# Final inventory. Count via globs (arrays), not `ls | wc -l`.
echo
echo "==> Installation complete. Inventory:"
inv_assets=( "$TARGET_DIR/assets"/* )
inv_scripts=( "$TARGET_DIR/scripts"/* )
echo "    SKILL.md:     $(test -f "$TARGET_DIR/SKILL.md" && echo "yes" || echo "MISSING")"
echo "    assets/:      ${#inv_assets[@]} files"
echo "    scripts/:     ${#inv_scripts[@]} files"

# Verify SARIF script dependency if the exporter was installed
if [ -f "$TARGET_DIR/scripts/sarif_export.py" ]; then
  echo
  echo "==> Verifying SARIF exporter dependencies"
  if python3 -c "import yaml" 2>/dev/null; then
    echo "    pyyaml: installed"
  else
    echo "    pyyaml: NOT installed (run: pip install pyyaml)"
  fi
fi

echo
echo "==> Next steps:"
echo "    1. Start Claude Code in any project: cd ~/project && claude"
echo "    2. Ask: 'What skills are available?'"
echo "    3. You should see 'premortem-code' in the list"
echo "    4. To run: 'Premortem-code standard mode on these changes'"
echo
echo "    Full tutorial: see TUTORIAL.md"
