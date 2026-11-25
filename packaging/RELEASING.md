# Releasing py-pdfocr

1. Set the new version in `pyproject.toml` and `src/py_pdfocr/__init__.py`,
   with an entry in both changelogs, the version in the READMEs and the
   title of `docs/DESCRIPCIÓN_es.md`. `tests/test_packaging.py` fails while
   they differ.

2. Commit, then publish:

   ```bash
   uv run python tools/release.py --notes-file NOTES.md
   ```

   This runs the tests (`tools/test.py`, each file in a process of its own);
   makes the wheel, the source package, the ZIP of the source and the
   AppImage in `dist/`; signs each of them, with `SHA256SUMS` and its
   signature, and checks every signature with only the public key; tags
   `vVERSION` with a signed tag; pushes to GitHub (`origin`) and Codeberg
   (`codeberg`); attaches the files, the signatures and the public key to
   the release on both; and uploads the deposit for Zenodo as a draft.
   `--dry-run` only shows the commands.

The AppImage (`tools/bundle-appimage.py`) downloads a Python of the
python-appimage project and appimagetool the first time, and keeps them in
`~/.cache/py-pdfocr-build`.

## The signing key

Everything is signed with the key `81870643CA221AF90C30554EBE6832CD35994948`,
the same as in the author's other projects. Its public half is
`packaging/RPM-GPG-KEY-py-pdfocr`, attached to every release. gpg asks for
the passphrase when the release signs.

## Zenodo

After the tag, `tools/zenodo.py collect` puts in `dist/zenodo/` the tree of
the tag as `py-pdfocr-VERSION-source.tar.gz`, its signature, a signed
`SHA256SUMS` and the public key, and checks every signature with only that
key. At the end of the release, `tools/zenodo.py upload` sends it to Zenodo
as a draft, with the metadata of `.zenodo.json`; if Zenodo already has a
published deposit with the same title, the draft is a new version of it.
The draft is never published by these tools: review it on Zenodo and
publish it there. The token (made at
https://zenodo.org/account/settings/applications/, with deposit:write and
deposit:actions) is kept once in the desktop keyring:

    secret-tool store --label="Zenodo token" service zenodo

`$ZENODO_TOKEN`, if it is set, goes before the keyring;
`tools/zenodo.py check-token` says whether there is one, without showing it.
`--no-zenodo` leaves the upload out. The description of the deposit is the
whole `README.md` of the tag, in HTML; the languages, the copyright, the
repository on GitHub, the programming language and the development status
are set on the draft through Zenodo's records API.
