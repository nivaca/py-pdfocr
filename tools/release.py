#!/usr/bin/env python3
"""Publish a release of py-pdfocr on GitHub (with gh) and Codeberg (with
tea): the tag vVERSION (the version of pyproject.toml), signed, with the wheel,
the source package, a ZIP of the source and the AppImage attached, each with its
signature (FILE.asc), with SHA256SUMS and its signature, and with the public key
that checks them all; the deposit of the release on Zenodo, as a draft; and
(--pypi) the wheel and the source package on PyPI.

Everything is signed with the project's key (SIGNING_KEY, the same in all the
author's projects), and every signature is checked, against the public key
published (packaging/RPM-GPG-KEY-py-pdfocr), before anything is published.

    uv run python tools/release.py [--notes TEXT | --notes-file FILE] [--pypi]
                                   [--no-build] [--no-appimage] [--no-tests] [--redo]
                                   [--only github|codeberg] [--no-zenodo] [--dry-run] [--yes]

In order, each step only if it is needed:

1. checks that the repository is on main, with nothing left to commit, that
   the versions agree (pyproject.toml and __init__.py), that the tools are
   installed (gh, tea, gpg), that the signing key is in gpg and, unless
   --no-zenodo, that there is a Zenodo token in $ZENODO_TOKEN or the keyring;
2. runs the tests, each file in a process of its own, at once
   (tools/test.py; unless --no-tests);
3. makes the wheel and the source package (uv build), the ZIP of the
   source (git archive of HEAD) and the AppImage (tools/bundle-appimage.py)
   in build/release/, unless --no-build (then those in build/release/ are
   used); then signs every file (tools/sign_release.py: FILE.asc,
   build/release/SHA256SUMS and its .asc), and checks each signature with
   only the public key that is published; gpg asks for the passphrase;
4. tags HEAD as vVERSION, a tag signed with the same key (git tag --sign),
   and checks it (git tag --verify). If the tag is already on another
   commit, it stops, unless --redo moves it;
5. collects the deposit for Zenodo in build/zenodo/ (tools/zenodo.py collect:
   the tree of the tag, signed, with SHA256SUMS and the public key, each
   signature checked with only that key);
6. pushes main and the tag to each remote (origin is GitHub, codeberg is
   Codeberg; --redo pushes the tag with --force);
7. on each forge, makes the release of the tag, or keeps the one there is,
   and attaches the files to it, replacing those of the same name;
8. with --pypi, uploads the wheel and the source package to PyPI (uv publish,
   with the API token in $UV_PUBLISH_TOKEN). PyPI never takes a file twice:
   with --redo, those already there are skipped, not replaced;
9. unless --no-zenodo, uploads build/zenodo/ to Zenodo and publishes it
   (tools/zenodo.py upload --publish), with a new DOI; with --zenodo-draft
   it is left as a draft, to publish by hand;
10. deletes build/release/ and build/zenodo/: the forges and Zenodo have
   what they held, and nothing of a release is kept here (there is no RPM,
   and dist/ is not used).

Before doing anything, it shows the commands it will run and asks; --yes
doesn't ask, --dry-run only shows them. The notes of a new release are
--notes, --notes-file, or else made by GitHub from the commits (on Codeberg,
none); a release that is there keeps its notes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
TAG = f"v{VERSION}"
TITLE = f"py-pdfocr {VERSION}"
BRANCH = "main"
# Lo que se publica se hace y se firma en build/release/, no en dist/: aquí no se guarda nada de una versión
# una vez publicada (no hay RPM)
OUT = "build/release"
WHEEL = f"{OUT}/py_pdfocr-{VERSION}-py3-none-any.whl"
SDIST = f"{OUT}/py_pdfocr-{VERSION}.tar.gz"
ZIP = f"{OUT}/py-pdfocr-{VERSION}.zip"
APPIMAGE = f"{OUT}/py-pdfocr-{VERSION}-x86_64.AppImage"
REMOTES = {"github": "origin", "codeberg": "codeberg"}
# La clave con que se firma todo lo publicado: la misma en todos los proyectos del autor (la que fija
# packaging/build-rpm.sh en los que hacen un RPM)
SIGNING_KEY = "81870643CA221AF90C30554EBE6832CD35994948"
PUBLIC_KEY = "packaging/RPM-GPG-KEY-py-pdfocr"  # (the public key published with every release)
SUMS = f"{OUT}/SHA256SUMS"


def zenodo_token() -> bool:
    """Whether tools/zenodo.py finds a Zenodo token, in $ZENODO_TOKEN or
    in the desktop keyring (secret-tool)."""
    tool = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools", "zenodo.py")
    done = subprocess.run([sys.executable, tool, "check-token"],
                          capture_output=True, check=False)
    return done.returncode == 0


def init_version() -> str:
    m = re.search(r'^__version__ = "([^"]+)"', (ROOT / "src/py_pdfocr/__init__.py").read_text(), re.MULTILINE)
    return m.group(1) if m else ""


class Release:
    """The steps, run (or only shown) in order."""

    def __init__(self, args):
        self.args = args
        self.planned: list[tuple[str, list[str]]] = []

    def read(self, *command, check=True) -> str:
        """The output of COMMAND (which only reads, so it runs even with --dry-run)."""
        out = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        if check and out.returncode != 0:
            sys.exit(f"release.py: {shlex.join(command)}: {(out.stderr or out.stdout).strip()}")
        return out.stdout.strip() if out.returncode == 0 else ""

    def plan(self, description: str, *command):
        self.planned.append((description, [str(c) for c in command]))

    def run_plan(self):
        print(f"Releasing {TAG}:")
        for description, command in self.planned:
            print(f"\n  # {description}\n  {shlex.join(command)}")
        print()
        if self.args.dry_run:
            return
        if not self.args.yes:
            answer = input("Run these commands? [y/N] ").strip().lower()
            if answer not in ("y", "yes", "s", "sí", "si"):
                sys.exit("Nothing done.")
        for description, command in self.planned:
            print(f"\n==> {description}", flush=True)
            if subprocess.run(command, cwd=ROOT, check=False).returncode != 0:
                sys.exit(f"release.py: failed: {shlex.join(command)}\nThe steps before it were done; after fixing "
                         "the cause, run the script again (with --redo if the tag was already moved).")
        print(f"\nReleased {TAG}.")

    # -------------------------------------------------------------- checks

    def check(self):
        tools = ["git", "uv", "gpg"] + [t for t, f in (("gh", "github"), ("tea", "codeberg")) if f in self.forges]
        for tool in tools:
            if not shutil.which(tool):
                sys.exit(f"release.py: {tool} is not installed")
        # Todo se firma, siempre: sin la clave no hay versión
        if subprocess.run(["gpg", "--batch", "--list-secret-keys", SIGNING_KEY], capture_output=True,
                          check=False).returncode != 0:
            sys.exit(f"release.py: the signing key {SIGNING_KEY} is not in this machine's gpg keyring; import it "
                     "first")
        if not (ROOT / PUBLIC_KEY).is_file():
            sys.exit(f"release.py: there is no {PUBLIC_KEY}, the public key published with the release")
        # (sin token se para aquí, antes de hacer nada, y no al final de la versión)
        if not self.args.no_zenodo and not self.args.dry_run and not zenodo_token():
            sys.exit("release.py: the upload to Zenodo needs a token (see tools/zenodo.py check-token); "
                     "--no-zenodo leaves it out")
        if self.args.pypi and not os.environ.get("UV_PUBLISH_TOKEN"):
            sys.exit("release.py: --pypi needs a PyPI API token in $UV_PUBLISH_TOKEN (make one at "
                     "https://pypi.org/manage/account/token/)")
        if init_version() != VERSION:
            sys.exit(f"release.py: pyproject.toml says {VERSION}, src/py_pdfocr/__init__.py says "
                     f"{init_version()}")
        branch = self.read("git", "rev-parse", "--abbrev-ref", "HEAD")
        if branch != BRANCH:
            sys.exit(f"release.py: on branch {branch}, not {BRANCH}")
        if self.read("git", "status", "--porcelain"):
            message = "there are changes not committed (see git status)"
            if not self.args.dry_run:
                sys.exit(f"release.py: {message}")
            print(f"release.py: (dry run) {message}", file=sys.stderr)

    def repos(self) -> dict[str, str]:
        """{forge: owner/name}, from the push addresses of the remotes."""
        found = {}
        for forge in self.forges:
            url = self.read("git", "remote", "get-url", "--push", REMOTES[forge], check=False)
            m = re.search(r"(github\.com|codeberg\.org)[:/]+([^/]+/[^/]+?)(?:\.git)?/?$", url)
            if not m or ("github" in m[1]) != (forge == "github"):
                sys.exit(f"release.py: the remote {REMOTES[forge]} does not push to {forge} (git remote -v)")
            found[forge] = m[2]
        return found

    # -------------------------------------------------------------- steps

    def tests(self):
        if not self.args.no_tests:
            # (a la vez, cada archivo en su proceso: tools/test.py)
            self.plan("Run the tests", "uv", "run", "python", "tools/test.py")

    def build(self):
        if self.args.no_build:
            for f in self.files:
                if not (ROOT / f).is_file():
                    sys.exit(f"release.py: there is no {f} (leave out --no-build to make it)")
            return
        if not self.args.dry_run:
            (ROOT / OUT).mkdir(parents=True, exist_ok=True)
        self.plan("Make the wheel and the source package", "uv", "build", "--out-dir", OUT)
        self.plan("Make the ZIP of the source", "git", "archive", "--format=zip", f"--prefix=py-pdfocr-{VERSION}/",
                  "--output", ZIP, "HEAD")
        if APPIMAGE in self.files:
            self.plan("Make the AppImage", "uv", "run", "python", "tools/bundle-appimage.py", "--output", OUT)

    def sign(self):
        """Every file published signed (FILE.asc), with SHA256SUMS and its signature, and each signature checked
        with only the public key published."""
        signed = [f for f in self.files if f != PUBLIC_KEY]
        self.plan("Sign the files, and check each signature with the published key", sys.executable,
                  "tools/sign_release.py", "--key", SIGNING_KEY, "--public", PUBLIC_KEY, "--sums", SUMS, *signed)
        self.files = signed + [f"{f}.asc" for f in signed] + [SUMS, f"{SUMS}.asc", PUBLIC_KEY]

    def tag(self):
        head = self.read("git", "rev-parse", "HEAD")
        tagged = self.read("git", "rev-parse", "--verify", "--quiet", f"refs/tags/{TAG}^{{commit}}", check=False)
        if tagged and tagged != head and not self.args.redo:
            sys.exit(f"release.py: {TAG} is already the tag of {tagged[:7]}, not of HEAD ({head[:7]}); --redo "
                     "moves it (and replaces the files of the releases)")
        # Una etiqueta de HEAD de antes de que se firmara todo se firma ahora, y se sube de nuevo, reemplazando la vieja
        unsigned = tagged == head and subprocess.run(["git", "tag", "--verify", TAG], cwd=ROOT, capture_output=True,
                                                     check=False).returncode != 0
        if tagged != head or unsigned:
            self.plan("Sign the tag of HEAD (it was not signed)" if unsigned
                      else "Move the tag to HEAD, signed" if tagged else "Tag HEAD, signed", "git", "tag", "--force",
                      "--sign", "--local-user", SIGNING_KEY, TAG, "--message", TITLE)
            self.plan("Check the signature of the tag", "git", "tag", "--verify", TAG)
        # El depósito para Zenodo, de la etiqueta (se sube al final)
        self.plan("Zenodo: collect the deposit in build/zenodo/", sys.executable, "tools/zenodo.py", "collect",
                  "--tag", TAG)
        for forge in self.forges:
            remote = REMOTES[forge]
            self.plan(f"Push {BRANCH} to {remote}", "git", "push", remote, BRANCH)
            if self.args.redo or unsigned:
                self.plan(f"Push the tag to {remote} (replacing it)", "git", "push", "--force", remote,
                          f"refs/tags/{TAG}")
                continue
            there = self.read("git", "ls-remote", "--tags", remote, f"refs/tags/{TAG}^{{}}", check=False)
            on_remote = there.split()[0] if there else ""
            if on_remote == head:
                continue
            if on_remote:
                sys.exit(f"release.py: on {remote}, {TAG} is the tag of {on_remote[:7]}; --redo moves it")
            self.plan(f"Push the tag to {remote}", "git", "push", remote, f"refs/tags/{TAG}")

    def notes(self, github: bool) -> list[str]:
        if self.args.notes_file:
            return ["--notes-file" if github else "--note-file", self.args.notes_file]
        if self.args.notes:
            return ["--notes" if github else "--note", self.args.notes]
        return ["--generate-notes"] if github else []

    def github(self, repo: str):
        exists = subprocess.run(["gh", "release", "view", TAG, "--repo", repo], cwd=ROOT,
                                capture_output=True, check=False).returncode == 0
        if exists:
            self.plan("GitHub: attach the files to the release (replacing those there)", "gh", "release", "upload",
                      TAG, *self.files, "--clobber", "--repo", repo)
        else:
            self.plan("GitHub: make the release", "gh", "release", "create", TAG, *self.files, "--title", TITLE,
                      "--verify-tag", *self.notes(True), "--repo", repo)

    def codeberg(self, repo: str):
        where = ["--repo", repo, "--login", self.args.tea_login]
        releases = self.tea_json("releases", "ls", "--limit", "50", *where)
        if any(TAG in (r.get("tagname"), r.get("tag")) for r in releases):
            names = {a.get("name") for a in self.tea_json("releases", "assets", "ls", TAG, *where)}
            old = [Path(f).name for f in self.files if Path(f).name in names]
            if old:
                self.plan("Codeberg: remove the files of the same name (tea cannot replace them)", "tea",
                          "releases", "assets", "delete", TAG, *old, "--confirm", *where)
            self.plan("Codeberg: attach the files to the release", "tea", "releases", "assets", "create", TAG,
                      *self.files, *where)
        else:
            assets = [a for f in self.files for a in ("--asset", f)]
            self.plan("Codeberg: make the release", "tea", "releases", "create", "--tag", TAG, "--title", TITLE,
                      *self.notes(False), *assets, *where)

    def tea_json(self, *command) -> list[dict]:
        """The rows tea gives in JSON, with its keys made plain ("tag-_name" is tagname)."""
        out = self.read("tea", *command, "--output", "json")
        try:
            rows = json.loads(out or "[]")
        except ValueError:
            sys.exit(f"release.py: tea {' '.join(command)}: not JSON: {out[:200]}")
        return [{re.sub("[^a-z]", "", k.lower()): v for k, v in r.items()} for r in rows]

    def pypi(self):
        self.plan("PyPI: upload the wheel and the source package", "uv", "publish",
                  "--check-url", "https://pypi.org/simple/", WHEEL, SDIST)

    def __call__(self):
        a = self.args
        self.forges = [a.only] if a.only else ["github", "codeberg"]
        self.files = [WHEEL, SDIST, ZIP] + ([] if a.no_appimage else [APPIMAGE]) + [PUBLIC_KEY]
        self.check()
        repos = self.repos()
        self.tests()
        self.build()
        self.sign()
        self.tag()
        for forge in self.forges:
            getattr(self, forge)(repos[forge])
        if a.pypi:
            self.pypi()
        if not a.no_zenodo:
            self.plan("Zenodo: upload the deposit" + (" as a draft (not published)" if self.args.zenodo_draft
                                                       else " and publish it"),
                      sys.executable, "tools/zenodo.py", "upload",
                      *([] if self.args.zenodo_draft else ["--publish"]))
        # Once all is published, nothing of it stays here: the forges and Zenodo have it
        self.plan("Delete what was published from build/ (the forges and Zenodo have it)", "rm", "-rf", OUT,
                  "build/zenodo")
        self.run_plan()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tools/release.py",
                                     description=f"Publish {TAG} on GitHub and Codeberg, with the wheel, the source "
                                                 "package, the ZIP and the AppImage, all signed, and upload "
                                                 "its deposit to Zenodo as a draft.")
    notes = parser.add_mutually_exclusive_group()
    notes.add_argument("--notes", metavar="TEXT", help="the notes of a new release")
    notes.add_argument("--notes-file", metavar="FILE", help="the notes of a new release, from FILE")
    parser.add_argument("--pypi", action="store_true",
                        help="also upload the wheel and the source package to PyPI ($UV_PUBLISH_TOKEN)")
    parser.add_argument("--no-build", action="store_true", help="use the files in build/release/ as they are")
    parser.add_argument("--no-appimage", action="store_true", help="without the AppImage")
    parser.add_argument("--no-tests", action="store_true", help="don't run the tests first")
    parser.add_argument("--redo", action="store_true",
                        help=f"move {TAG} to HEAD if it is on another commit (here and on the remotes), and "
                             "replace the files of the releases")
    parser.add_argument("--only", choices=("github", "codeberg"), help="publish on one forge only")
    parser.add_argument("--tea-login", default="codeberg", help="the login of tea for Codeberg (default: codeberg)")
    parser.add_argument("--no-zenodo", action="store_true",
                        help="don't upload the deposit to Zenodo (by default it is uploaded and "
                             "published, with the token in $ZENODO_TOKEN or the keyring)")
    parser.add_argument("--zenodo-draft", action="store_true",
                        help="upload it to Zenodo as a draft, not published")
    parser.add_argument("-n", "--dry-run", action="store_true", help="only show the commands")
    parser.add_argument("-y", "--yes", action="store_true", help="don't ask before running them")
    args = parser.parse_args(argv)
    if args.notes_file:
        args.notes_file = str(Path(args.notes_file).resolve())
    Release(args)()


if __name__ == "__main__":
    main()
