# gitlarp

Tiny changes. Many commits. Numbers go up.

```bash
gitlarp commit
```

Run from anywhere inside a Git repo. Automatically stages and commits each
changed file, with messages such as `Add hello.txt`, `Update src/main.rs`, or
`Delete old.txt`. Includes staged changes, unstaged changes, and untracked files;
ignored files stay ignored. A partially staged file is committed in full.
Other files' staged changes stay separate until their turn.

## Commit modes

```bash
gitlarp mode file
gitlarp mode line
gitlarp mode word
gitlarp mode
gitlarp commit
```

Choose one mode, then run `gitlarp commit` as usual. `gitlarp mode` without an
argument displays the current mode. The setting is saved locally as
`gitlarp.mode` in Git configuration and does not get committed or shared with
other clones. The default is `file`.

- `file`: one commit per changed file, as before.
- `line`: one commit per inserted, deleted, or replaced text line. Replacing
  one old line with one new line counts as one change.
- `word`: one commit per inserted, deleted, or replaced whitespace-delimited
  token. Spaces, tabs, and newlines are separators; punctuation stays attached
  to its word. Leading whitespace travels with its token, and trailing
  whitespace is a separate token so formatting changes are preserved.

For example, changing `hello world` to `goodbye universe` makes one commit in
line mode, or two in word mode. Unchanged text produces no additional commits.
Try editing a sentence in this README, then run `gitlarp mode word` followed
by `gitlarp commit`. Inspect the
New files are built up incrementally and deleted files are removed incrementally.
Binary/non-UTF-8 files, symlinks, submodule pointers, empty files, and changes
only to executable permissions use a single commit per file.

Line and word modes require Python 3 (included by the Nix and Arch packages).
They build intermediate versions in a temporary Git index without rewriting
your working files. Hooks inspecting working files therefore see the final
contents; hooks inspecting staged contents see the intermediate step. Intermediate
commits may contain incomplete code. If a hook or signing fails, earlier commits
remain and staging may differ from HEAD; your working-file contents remain in
place. Fix the failure and rerun `gitlarp commit` to continue from HEAD.

## Install on Linux

Clone this project and install:

```bash
git clone https://github.com/atMiaobo/commit_larp.git
cd commit_larp
sudo make install
```

This installs `gitlarp` into `/usr/local/bin` for all users. With that directory
on your `PATH` (the usual Linux default), run `gitlarp commit` from any Git repo;
you no longer need the source directory. Requires Bash, Git, and coreutils at
runtime, plus Python 3 for line/word modes and Make for installation.
No compilation is needed.
Without Make, the equivalent install command is
`sudo install -Dm755 gitlarp /usr/local/bin/gitlarp`.

For a user-only installation without sudo:

```bash
make install PREFIX="$HOME/.local"
```

Ensure `$HOME/.local/bin` is on your `PATH`. To uninstall, use
`sudo make uninstall`, or `make uninstall PREFIX="$HOME/.local"` respectively.
Re-run the install command after updating the source to upgrade.

On NixOS, use the Nix package below so dependencies and command discovery are
managed by Nix.

## Arch Linux packaging

A development package recipe is available in
[`packaging/arch`](packaging/arch/README.md), including build and AUR submission
instructions. It is not published to the AUR or official repositories yet.

## Install on NixOS

With flakes enabled, from this directory:

```bash
nix run path:. -- --help
nix profile install path:.
```

This installs the command on your user's `PATH`, so you can use `gitlarp commit`
in any repository. The first flake command resolves
nixpkgs and creates `flake.lock`; keep that file in Git for reproducible builds.
The explicit `path:.` also includes files that are not yet tracked by Git.

Without flakes, using your configured nixpkgs channel:

```bash
nix-build
./result/bin/gitlarp --help
nix-env -i -f .
```

For a **system-wide installation for all users**, put this directory somewhere
persistent and add the package to your NixOS configuration (usually
`/etc/nixos/configuration.nix`):

```nix
environment.systemPackages = [
  (import /absolute/path/to/commit_larp { inherit pkgs; })
];
```

Apply it with `sudo nixos-rebuild switch` (using your usual `--flake` argument
if your system configuration uses flakes). Every user can then run
`gitlarp commit` from any Git repository. Nix copies the program into its store;
the source directory is only needed again when rebuilding or updating.

## Try it in this project

Create a local repository (no GitHub account or remote needed):

```bash
cd /home/mihao/Documents/Projects/commit_larp
git init -b main
```

If you haven't configured your Git identity, set it for this repo:

```bash
git config user.name "Your Name"
git config user.email "you@example.com"
```

Run directly, with no installation required:

```bash
./gitlarp commit
git log --oneline
```

Or use `nix run path:. -- commit`. No `git add` step is needed: gitlarp does
that for each file. Once installed with `nix profile install path:.`, the same
command is simply `gitlarp commit`.

## Behavior

- Shows ahead/behind counts against the locally cached upstream branch when one
  exists. Run `git fetch` yourself if you want that comparison refreshed.
- Finds new work against local `HEAD`: differences already committed locally
  cannot produce new commits without rewriting history. Existing commits are
  left intact. No remote is required, including for a repo's first commits.
- Does not fetch, pull, push, or overwrite the regular `git commit` command.
  The command is `gitlarp commit`.
- Renames become a deletion commit and an addition commit.
- Git identity, hooks, and signing settings work normally. If a commit fails,
  processing stops; earlier commits remain and the failed file may be staged.
- Refuses unresolved conflicts, detached HEAD, and ongoing merge/rebase operations.
- Submodule pointer changes can be committed; uncommitted files inside a submodule
  must be committed from inside that submodule first.
- Commits every non-ignored changed file: review your files and `.gitignore`
  before running. Avoid editing files or running other Git writers during a run.

## Check

```bash
bash tests/integration.sh
```
