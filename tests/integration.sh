#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
test_root=$(mktemp -d)
trap 'rm -rf -- "$test_root"' EXIT
export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_GLOBAL=/dev/null
export GIT_AUTHOR_NAME='Gitlarp Test' GIT_AUTHOR_EMAIL='test@example.invalid'
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME" GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE

git init -q "$test_root/repo"
cd "$test_root/repo"
printf 'one\n' > first
printf 'two\n' > 'space name'
printf 'ignored\n' > .gitignore
printf 'secret\n' > ignored
bash "$script_dir/gitlarp" commit
[[ $(git rev-list --count HEAD) -eq 3 ]]
[[ -z $(git status --porcelain) ]]
[[ -f ignored ]]

printf 'staged\n' >> first
git add first
printf 'unstaged\n' >> first
rm 'space name'
printf 'literal\n' > ':wild*card'
printf 'newline\n' > $'line\nbreak'
mkdir nested
cd nested
bash "$script_dir/gitlarp" commit
cd ..
[[ $(git rev-list --count HEAD) -eq 7 ]]
[[ -z $(git status --porcelain) ]]
[[ $(git show HEAD:first) == $'one\nstaged\nunstaged' ]]
while IFS= read -r revision; do
    changed=()
    mapfile -d '' -t changed < <(git diff-tree --root --no-commit-id --no-renames --name-only -r -z "$revision")
    [[ ${#changed[@]} -eq 1 ]]
done < <(git rev-list HEAD)
bash "$script_dir/gitlarp" commit
[[ $(git rev-list --count HEAD) -eq 7 ]]

git clone -q --bare . "$test_root/remote.git"
git remote add origin "$test_root/remote.git"
git fetch -q origin
branch=$(git symbolic-ref --short HEAD)
git branch --set-upstream-to="origin/$branch" >/dev/null
printf 'remote comparison\n' >> first
bash "$script_dir/gitlarp" commit
[[ $(git rev-list --count '@{upstream}..HEAD') -eq 1 ]]

printf 'pending\n' >> first
git rev-parse HEAD > "$(git rev-parse --git-path MERGE_HEAD)"
if bash "$script_dir/gitlarp" commit; then
    printf 'Expected merge refusal\n' >&2
    exit 1
fi
rm "$(git rev-parse --git-path MERGE_HEAD)"
[[ $(git rev-list --count HEAD) -eq 8 ]]
printf 'All integration checks passed.\n'
python3 "$script_dir/tests/modes.py"
