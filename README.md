# gitlarp

One changed file. One commit. Numbers go up.

```bash
gitlarp commit
```

Run from anywhere inside a Git repo. Automatically stages and commits each
changed file, with messages such as `Add hello.txt`, `Update src/main.rs`, or
`Delete old.txt`. Includes staged changes, unstaged changes, and untracked files;
ignored files stay ignored. A partially staged file is committed in full.
Other files' staged changes stay separate until their turn.

## Install on NixOS

With flakes enabled, from this directory:

```bash
nix run path:. -- --help
nix profile install path:.
```

Then use `gitlarp commit` in any repository. The first flake command resolves
nixpkgs and creates `flake.lock`; keep that file in Git for reproducible builds.
The explicit `path:.` also includes files that are not yet tracked by Git.

Without flakes, using your configured nixpkgs channel:

```bash
nix-build
./result/bin/gitlarp --help
nix-env -i -f .
```

For a declarative installation, put this directory somewhere persistent and add
the package to your NixOS configuration:

```nix
environment.systemPackages = [
  (import /absolute/path/to/commit_larp { inherit pkgs; })
];
```

Then rebuild your NixOS configuration as usual. Alternatively, put the executable
`gitlarp` script in a directory on your `PATH`; it needs Bash, Git, and coreutils.
You can try it immediately with `bash /absolute/path/to/commit_larp/gitlarp commit`.

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
