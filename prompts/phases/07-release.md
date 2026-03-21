# Phase 7: Release

## Responsible agent
`devops`

## Objective
Create a versioned release of the project: merge to main, tag, changelog, and GitHub release.

## Prerequisites
- Phase 5 (Review) validated OR explicit user decision to release current state
- All target features implemented and tested

## Instructions

You are in **Phase 7 — Release**. You must create a proper versioned release.

### Step 1: Pre-release checks
1. Verify all tests pass on the release branch
2. Verify no uncommitted changes
3. Verify the branch is up to date with its base
4. Review the diff between current main and the release branch

### Step 2: Versioning (Semantic Versioning)
1. Determine the version number following semver:
   - **Major** (X.0.0): breaking changes, major redesigns
   - **Minor** (0.X.0): new features, non-breaking
   - **Patch** (0.0.X): bug fixes, minor improvements
2. For initial releases: start at `v0.1.0` (pre-1.0 = not production-ready)
3. Confirm the version with the user

### Step 3: Changelog
1. Generate a changelog from commits since the last tag (or initial commit if first release)
2. Group changes by category:
   - **Features**: new functionality
   - **Fixes**: bug fixes
   - **Improvements**: enhancements to existing features
   - **Infrastructure**: CI/CD, tooling, dependencies
3. Write in human-readable format, not just commit messages

### Step 4: Merge and tag
1. Merge the release branch into main (ask user before proceeding)
2. Create an annotated git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
3. Push the tag: `git push origin vX.Y.Z`

### Step 5: GitHub Release
1. Create a GitHub release using `gh release create`
2. Include the changelog as the release body
3. Mark as pre-release if version is < 1.0.0

### Step 6: Post-release
1. Verify the release is visible on GitHub
2. If applicable, trigger deployment pipeline
3. Update any version references in the codebase (package.json, etc.)

## Expected deliverable
- Tagged release on main branch
- GitHub release with changelog
- Clean state: main = release, develop can continue

## Validation criteria
- [ ] Version follows semver
- [ ] Tag exists on main branch
- [ ] GitHub release is published with changelog
- [ ] All tests pass on the tagged commit
- [ ] User has confirmed the release
