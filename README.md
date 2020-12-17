# SurroRTG: Surrogate device SDK

## Python version

For enabling reproducable dependency installations, this project uses `pipenv`.
Pipenv in this projects requires Python version 3.7 or higher, which can be
installed for example with `pyenv`, <https://github.com/pyenv/pyenv>.
You can check your current version with `python --version`.
Follow the steps below to install the correct Python version if not already found.

### Installing Python 3.7 with pyenv

To install all necessary dependencies for pyenv and Python, run the following command:

```
sudo apt-get update && sudo apt-get upgrade && sudo apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl git
```

To install pyenv with the official installer, run `curl https://pyenv.run | bash`.
Then, to add pyenv to your path, add these three lines to the end of your `~/.bashrc`
file using your preferred text editor.

```
export PATH="/home/$USER/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

Then run `source ~/.bashrc`.

Next, install the correct Python version with `pyenv`, by running
`pyenv install 3.7.8`. Then, to enable the correct Python version to be used
for SurroRTG SDK, navigate to the root of your cloned `surrortg-sdk` repository
in your terminal, and run `pyenv local 3.7.8`.

## Installing dependencies

To install all of the dependencies, run first `pip install pipenv` and then
`pipenv sync`.

Then you can enter the virtual environment with `pipenv shell` (and exit with
`exit`). There are also scrotps such as `pipenv run arcade` for starting test
games, check Pipfile for more scripts.

## Development

### Code style

We're following PEP8, and have the formatter `black` and linter `flake8` setup.
These tools are run in Bitbucket to ensure properly formatted code, but
use of pre-commit hooks is highly recommended.

For this purpose, there are settings for pre-commit tool in the project. To
use it, run `pipenv sync --dev`.
Then run `pre-commit install` in the project root.

### Running

Enter the virtual environment with `pipenv shell`.
Then run `python -m <module_name>` in project the root,
e.g `python -m games.rvr.game`.
To exit the shell simply run `exit`.

### Running the Dummy game

Create a new game at `dev.surrogate.tv/admin`. Then start the GE, and submit
options for single player.

Next, copy `games/dummy_game/config_sample.toml` file to your preferred location,
and add the game's `device_id`, `token` and `id` to it. Then save `surrortg`
streamer binary to your machine.

Start the Python robot from the project root with:  
`pipenv run dummy --conf=<PATH_TO_YOUR_CONFIG_TOML>`

and the surrortg streamer from the save location with:  
`./surrortg --conf=<PATH_TO_YOUR_CONFIG_TOML>`

Now you should be able to queue and play the game.

## Protocol

Commands from player are sent as JSON with following template:

```javascript
{
  type: <type>,
  id: <input-id>,
  command: <type-specific json object>
}
```

Refer to device classes for message format definitions for specific types

## Runnning Python unit tests

Then go through the unittests the tests by running `pipenv run tests`

## Documentation

To build the documentation, first run `pipenv sync --dev`.

Then to build docs page or pdf docs use  
`pipenv run docs` or `pipenv run pdf-docs`.

To also open the docs page or pdf, you can add `--` before the command
and `-f` to open on Firefox or `-c` to open in Chromium.
For example: `pipenv run -- docs -f`

Also to serve the docs page in <http://localhost:8000> you can use
`pipenv run -- docs -s`

After building, the documentation can be found in
`docs/build/html/index.html` or `docs/build/latex/surrortgsdk.pdf`
