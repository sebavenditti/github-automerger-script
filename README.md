# GitHub Automerger Script

Brief: this script allows you to merge 2 branches of your GitHub repository. It uses the GitHub API to create a Pull Request and attempt to accept it. If it fails, it exits with a non-zero exit code (so, for example, you can use it to make a Jenkins job to fail).


## Usage:

```
python github-automerger.py <auth_token> <repo> <base-branch> <head-branch> [<assignee-login>]
```

↳  auth_token: an auth token to access the GitHub API (see: [Personal access tokens](https://github.com/settings/tokens)).

↳  repo: the repository that should be used. Format: **repo-owner/repo-name**

↳  base-branch: the branch where you want the changes to be applied.

↳  head-branch: the branch that contains what you would like to be applied. Format: **repo-owner:head-branch-name**

↳  assignee-login: optional parameter that can be used to specify the login (username) of the user to which the pull request should be assigned in case of a conflict while attempting to merge. If not provided, the pull request will be unassigned.'


## Example: 

To get all the changes from *master* merged to *a feature branch*, you can schedule a Jenkins job that runs every 15 minutes and executes the following shell command:

```
python github-automerger.py fe6a3gf1bfdef1egc083ad1b8g24635a6a1c4442 repo-owner/repo-name your-feature-branch master your-username
```

## Recommended reading:

https://help.github.com/articles/using-pull-requests/
