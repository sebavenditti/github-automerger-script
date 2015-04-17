# Github Automerger Script

Brief: this script allows you to merge 2 branches of your GitHub repository. It uses the GitHub API to create a Pull Request and attempt to accept it. If it fails, it exits with a non-zero exit code (so, for example, you can use it to make a Jenkins job to fail).
