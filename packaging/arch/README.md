# Arch Linux packaging

This is a development package recipe for `gitlarp-git`. It downloads the latest
`main` branch from GitHub and installs the command as `/usr/bin/gitlarp`.
It has not been submitted to the AUR or an official Arch repository.

## Build and install on Arch

Install the build tools once:

```bash
sudo pacman -S --needed base-devel git
```

From this directory, as a regular user:

```bash
makepkg -si
gitlarp --help
```

`makepkg` computes the version from Git history, runs the integration tests,
builds a `.pkg.tar.zst` package, and uses pacman to install it. A built package
can also be distributed for installation with `sudo pacman -U <package-file>`.

## Prepare an AUR submission

1. Choose a project license and add its license file to the source repository.
   The project currently has no declared license, so the recipe intentionally
   leaves `license` unset. Add the matching SPDX identifier to the recipe and
   install the license file under `/usr/share/licenses/$pkgname/` when required.
2. Push the source changes to GitHub and test `makepkg -si` on Arch.
3. Create an AUR account, register your SSH public key, and verify that the
   package name is available and complies with AUR submission guidelines.
4. Clone `ssh://aur@aur.archlinux.org/gitlarp-git.git` into a separate directory.
   Copy the tested `PKGBUILD` there, then generate metadata using
   `makepkg --printsrcinfo > .SRCINFO`.
5. Commit and push `PKGBUILD` and `.SRCINFO` in that AUR repository. Do not upload
   the application source or built package to the AUR Git repository.

After publication, users with an AUR helper can install using
`yay -S gitlarp-git` or `paru -S gitlarp-git`, then run `gitlarp commit`.
These installation commands will not work until the package is published.

`pacman -S gitlarp-git` requires the package to be in a configured binary
repository. The AUR is a separate collection of build recipes. Official
repository inclusion is managed by Arch package maintainers; alternatively,
you can host a custom binary repository that users explicitly configure.

References: [PKGBUILD](https://man.archlinux.org/man/PKGBUILD.5.en),
[makepkg](https://man.archlinux.org/man/makepkg.8.en),
[AUR submission guidelines](https://wiki.archlinux.org/title/AUR_submission_guidelines).
