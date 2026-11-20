# Git

The Git configuration file applies to every repository on both machines. It
establishes three properties: a verifiable identity, a rebase-oriented workflow,
and a set of short aliases for routine commands.

## Identity and signing

Every commit and tag carries an [OpenPGP](../glossary.md#openpgp) signature made
with the key below. The commit editor receives the staged diff so that the final
review occurs at commit time rather than after the fact.

| Setting           | Value              | Effect                                          |
| :---------------- | :----------------- | :---------------------------------------------- |
| `user.signingkey` | `6A5CDB74309F53EA` | The OpenPGP key used for signatures             |
| `gpg.format`      | `openpgp`          | Signatures use OpenPGP rather than SSH or X.509 |
| `commit.gpgsign`  | `true`             | Commits are signed                              |
| `tag.gpgSign`     | `true`             | Tags are signed                                 |
| `commit.verbose`  | `true`             | The commit editor shows the staged diff         |

Credentials are delegated to the GitHub CLI.

| Host              | Credential provider |
| :---------------- | :------------------ |
| `github.com`      | `gh`                |
| `gist.github.com` | `gh`                |

## Defaults

The following settings define the repository workflow. Rebasing preserves a
linear history, conflict markers retain the common ancestor, and
[recorded resolutions](../glossary.md#rerere) are reused across rebases.

| Setting                | Value                             | Effect                                                        |
| :--------------------- | :-------------------------------- | :------------------------------------------------------------ |
| `init.defaultBranch`   | `main`                            | New repositories start on `main`                              |
| `pull.rebase`          | `true`                            | Pull rebases local commits instead of creating a merge commit |
| `merge.conflictstyle`  | [`zdiff3`](../glossary.md#zdiff3) | Conflict markers include the common ancestor                  |
| `rerere.enabled`       | `true`                            | Reuses recorded conflict resolutions                          |
| `rebase.autoSquash`    | `true`                            | Reorders `fixup!` and `squash!` commits in the todo list      |
| `rebase.autoStash`     | `true`                            | Stashes and restores uncommitted changes around a rebase      |
| `push.autoSetupRemote` | `true`                            | The first push sets the upstream branch                       |
| `push.followTags`      | `true`                            | Pushes annotated tags reachable from the pushed commits       |
| `fetch.prune`          | `true`                            | Deletes remote-tracking branches that no longer exist         |
| `diff.algorithm`       | `histogram`                       | Uses the histogram diff algorithm                             |
| `help.autocorrect`     | `prompt`                          | Asks before running a command close to a mistyped one         |

## Aliases

The everyday shortcuts abbreviate commands that are frequent but lengthy. The
`sw` alias is unrelated to the `sw` wallpaper utility.

| Alias     | Expands to                               | Effect                                   |
| :-------- | :--------------------------------------- | :--------------------------------------- |
| `br`      | `branch`                                 | List branches                            |
| `co`      | `checkout`                               | Switch to a ref                          |
| `sw`      | `switch`                                 | Switch branches                          |
| `ci`      | `commit`                                 | Commit staged changes                    |
| `cm`      | `commit --message`                       | Commit with an inline message            |
| `a`       | `add`                                    | Stage files                              |
| `aa`      | `add --all`                              | Stage every change                       |
| `s`       | `status -sb`                             | Short status with branch information     |
| `unstage` | `restore --staged`                       | Unstage files without discarding changes |
| `r`       | `remote`                                 | List remotes                             |
| `ra`      | `remote add`                             | Add a remote                             |
| `rrm`     | `remote remove`                          | Remove a remote                          |
| `p`       | `push`                                   | Push the current branch                  |
| `pl`      | `pull`                                   | Pull, with rebasing from `pull.rebase`   |
| `pom`     | `push origin main`                       | Push the main branch to origin           |
| `last`    | `log -1 --stat`                          | Inspect the latest commit                |
| `lg`      | `log --oneline --graph --decorate --all` | Browse the whole history graph           |
| `vsig`    | `log --show-signature -1`                | Verify the latest signature              |

A second group changes history or overwrites remote state. I list these
separately because each can discard work, publish it irreversibly, or commit
more than the staged set:

| Alias   | Command                                                          | Effect                                                        |
| :------ | :--------------------------------------------------------------- | :------------------------------------------------------------ |
| `ca`    | `commit --amend --no-edit`                                       | Amends the current commit with staged changes                 |
| `undo`  | `reset --soft HEAD~1`                                            | Drops the last commit and leaves its changes staged           |
| `wip`   | `!git add -A && git commit -m 'wip: work in progress [skip ci]'` | Commits every change, including untracked files               |
| `pushf` | `push --force-with-lease`                                        | Force-pushes, refusing when the remote branch has new commits |
