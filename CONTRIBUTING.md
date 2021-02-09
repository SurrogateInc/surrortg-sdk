# Contributing

We are looking for anything ranging from documentation improvements and
bugfixes to new features. Bug reports and feature requests through
[issues](https://github.com/SurrogateInc/surrortg-sdk/issues) are also
greatly appreciated.

New features and game examples might not be accepted if they do not fit the
scope of the project, so please first discuss the change you wish to make via
[issue](https://github.com/SurrogateInc/surrortg-sdk/issues) or though our
[community discord](https://discord.com/invite/surrogatetv).

Particularly larger custom games might make more sense as separate projects.

At Surrogate, we want to ensure that everyone gets to share their ideas in a
healthy environment. Stay constructive when commenting on someone else’s
thoughts and be respectful of differing viewpoints. Offensive, harmful or
inappropriate comments, issues and pull requests will get removed.

## Pull request process

1. Ensure that you have tested the changes with Python 3.7 and have used the
   latest Pipfile.lock (`pipenv sync --dev`).
2. Update the README.md and the documentation with details of changes if they
   change the current documented behaviour.
3. Divide the work into logical commits, and follow the existing commit style.
   For example documentation changes related commit should start with 'docs: '
4. Make sure that the existing Github actions report, such as unit tests,
   linter and formatter, report success. (These are triggered automatically
   after each commit).
5. The pull request will be reviewed by someone from SurrogateInc, and if the
   changes are accepted, the reviewer will merge the request. If the change
   cannot be accepted, you'll get response explaining the reasoning.
