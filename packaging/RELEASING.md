# Releasing py-pdfocr

1. Set the new version in `pyproject.toml` and `src/py_pdfocr/__init__.py`,
   with an entry in both changelogs, the version in the READMEs and the
   title of `docs/DESCRIPCIÓN_es.md`. `tests/test_packaging.py` fails while
   they differ.

2. Commit, then publish:

   ```bash
   uv run python tools/release.py --notes-file NOTES.md
   ```

   This runs the tests; makes the wheel, the source package, the ZIP of the
   source and the AppImage in `dist/`; tags `vVERSION`; pushes to GitHub
   (`origin`) and Codeberg (`codeberg`); and attaches the files to the
   release on both. `--dry-run` only shows the commands.

The AppImage (`tools/bundle-appimage.py`) downloads a Python of the
python-appimage project and appimagetool the first time, and keeps them in
`~/.cache/py-pdfocr-build`.
