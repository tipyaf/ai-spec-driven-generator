# Phase 7: Release

## Responsible agent
`devops`

## Objective
Create a versioned release of the project using a release branch workflow: `develop` → `release/vX.Y.Z` → `main` (tag) → merge back to `develop`.

## Prerequisites
- Phase 5 (Review) validated OR explicit user decision to release current state
- All target features implemented and tested on `develop`

## Git Flow

```
develop ──────────────────────────────────────────────────►
    │                                          ▲
    └── release/vX.Y.Z ──► main (tag vX.Y.Z) ─┘
```

**Rule**: `main` only receives release merges. No direct commits to `main`.

## Instructions

You are in **Phase 7 — Release**. You must create a proper versioned release.

### Step 1: Pre-release checks
1. Verify the `develop` branch has no uncommitted changes
2. Verify `develop` is up to date with `origin/develop`
3. Review the diff between current `main` and `develop`
4. List all commits that will be included in the release

### Step 2: Versioning (Semantic Versioning)
1. Determine the version number following semver based on the CONTENT of the release:
   - **Major** (X.0.0): breaking changes, major redesigns, incompatible API changes
   - **Minor** (0.X.0): new features, non-breaking additions
   - **Patch** (0.0.X): bug fixes, minor improvements, no new features
2. For initial releases: start at `v0.1.0` (pre-1.0 = not production-ready)
3. Confirm the version with the user before proceeding

### Step 3: Create the release branch
1. Create branch `release/vX.Y.Z` from `develop`
2. On this branch, perform any release-specific changes:
   - Update version in `package.json` (if applicable)
   - Generate/update CHANGELOG.md
   - Any last-minute fixes specific to the release
3. Commit these changes on the release branch

### Step 4: Changelog
1. Generate a changelog from commits since the last tag (or initial commit if first release)
2. Group changes by category:
   - **Features**: new functionality
   - **Fixes**: bug fixes
   - **Improvements**: enhancements to existing features
   - **Infrastructure**: CI/CD, tooling, dependencies
3. Write in human-readable format, not just commit messages
4. Save as `CHANGELOG.md` at the project root (append to existing if present)

### Step 5: Merge to main and tag
1. **Ask user confirmation before merging**
2. Merge the release branch into `main`: `git checkout main && git merge release/vX.Y.Z --no-ff`
3. Create an annotated git tag on `main`: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
4. Push `main` and the tag: `git push origin main && git push origin vX.Y.Z`

### Step 6: Merge back to develop
1. Merge `main` back into `develop` to sync any release-specific changes: `git checkout develop && git merge main`
2. Push `develop`: `git push origin develop`
3. Delete the release branch: `git branch -d release/vX.Y.Z && git push origin --delete release/vX.Y.Z`

### Step 7: GitHub Release
1. Create a GitHub release using `gh release create vX.Y.Z --target main`
2. Include the changelog as the release body
3. Mark as pre-release if version is < 1.0.0

### Step 8: Post-release verification
1. Verify the release is visible on GitHub
2. Verify `main` has the tag
3. Verify `develop` includes the release changes
4. If applicable, trigger deployment pipeline

## Expected deliverable
- Release branch merged into `main`
- Annotated git tag on `main`
- GitHub release with changelog
- `develop` synced with `main`
- Clean state: no dangling release branch

## Validation criteria
- [ ] Version follows semver based on release content
- [ ] Release branch was created from `develop`
- [ ] `main` only contains release merges (no direct commits)
- [ ] Tag exists on `main` branch
- [ ] GitHub release is published with changelog
- [ ] `develop` is synced back with `main`
- [ ] Release branch is deleted
- [ ] User has confirmed the release before merge
