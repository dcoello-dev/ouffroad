# CI/CD Setup - Automated Releases

Quick reference for the automated release system.

## How It Works

The release workflow automatically creates GitHub releases when you change the version in `__init__.py`.

---

## Creating a Release

### 1. Update Version

Edit `src/ouffroad/__init__.py`:

```python
__version__ = "0.0.5"  # Change this
__date__ = "05/12/2025"
```

### 2. Commit and Push

```bash
git add src/ouffroad/__init__.py
git commit -m "Bump version to 0.0.5"
git push origin main
```

### 3. Automatic Process

GitHub Actions will:
- ✅ Detect version change
- ✅ Build Python package
- ✅ Build frontend
- ✅ Generate changelog
- ✅ Create Git tag `v0.0.5`
- ✅ Create GitHub release
- ✅ Upload artifacts

---

## What Gets Released

Each release includes:
- **Python Wheel**: `ouffroad-{version}-py3-none-any.whl`
- **Source Distribution**: `ouffroad-{version}.tar.gz`
- **Changelog**: Auto-generated from commits
- **Frontend Build**: Available as artifact (90 days)

---

## Workflow Files

- `.github/workflows/release.yml` - Automated releases
- `.github/workflows/ci.yml` - Existing CI tests

---

## Troubleshooting

**Release not created?**
- Check if tag already exists: `git tag -l`
- Verify workflow ran: GitHub Actions tab
- Check workflow logs for errors

**Want to skip release?**
- Don't change `__init__.py` version
- Or push to `develop` branch instead

---

## Manual Release (if needed)

```bash
# Create tag manually
git tag -a v0.0.5 -m "Release v0.0.5"
git push origin v0.0.5

# Then create release on GitHub UI
```
