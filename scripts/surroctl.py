#!/usr/bin/python3
import fileinput
import os
import sys
from uuid import UUID

import click
import toml

TARGETS = {
    "all": "controller srtg srtg-watcherstream",
    "controller": "controller",
    "streamer": "srtg",
    "watcherstream": "srtg-watcherstream",
}


def command(command):
    click.echo(f"Executing '{command}'")
    os.system(command)


def validate_uuid4(uuid):
    try:
        UUID(uuid, version=4)
    except ValueError:
        return False
    return True


def get_token():
    click.echo(toml.load("/etc/srtg/srtg.toml")["game_engine"]["token"])


def set_token(token):
    # Verify token lengths
    uuids = token.split("/")
    if len(uuids) != 2 or len(uuids[0]) != 36 or len(uuids[1]) != 8 * 36:
        click.echo("Not a valid token")
        return

    # Verify token structure
    uuids = [uuids[0]] + [
        uuids[1][i : i + 36] for i in range(0, len(uuids[1]), 36)
    ]
    if not all(map(validate_uuid4, uuids)):
        click.echo("Not a valid token")
        return

    # Set token
    try:
        token_line_found = False
        for line in fileinput.input("/etc/srtg/srtg.toml", inplace=True):
            if line.startswith("token"):
                print(f'token = "{token}"')
                token_line_found = True
            else:
                print(line, end="")
    except PermissionError:
        click.echo(
            "\nSetting token requires use of sudo, try:\n\n"
            f"sudo surroctl token {token}"
        )
        return

    if not token_line_found:
        click.echo("Token could not be updated")
        return

    # Restart services
    os.system(f"sudo systemctl restart {TARGETS['all']}")
    click.echo("Token set")


def get_path():
    with open("/usr/lib/systemd/system/controller.service") as f:
        for line in f.readlines():
            if line.startswith("Environment="):
                click.echo(
                    line.split("=")[-1].rstrip().replace(".", "/") + ".py"
                )
                return
    click.echo("Path not found")


def set_path(path):
    # Remove start if path is from the root or if has any leading slashes
    path = path.replace("home/pi", "")
    path = path.replace("surrortg-sdk/", "")
    path = path.lstrip("/")

    # remove .py ending, and modify slashes to dots
    path = path.rstrip(".py")
    path = path.replace("/", ".")

    # Replace line in config
    path_line_found = False
    for line in fileinput.input(
        "/home/pi/surrortg-sdk/scripts/controller-rpi.service", inplace=True
    ):
        if line.startswith("Environment=GAME_MODULE="):
            print(f"Environment=GAME_MODULE={path}")
            path_line_found = True
        else:
            print(line, end="")

    if not path_line_found:
        click.echo("Path could not be updated")
        return

    click.echo(f"Using path: {path}")

    # Restart the service
    command("/home/pi/surrortg-sdk/scripts/setup-systemd.sh")


def echo_versions():
    image_version = "Not available"
    with open("/etc/os-release") as f:
        for line in f.readlines():
            if line.startswith('SRTG_IMG_VERSION="'):
                image_version = line.replace('SRTG_IMG_VERSION="', "").rstrip(
                    '"\n'
                )
                break

    sdk_version = "Not available"
    with open("/home/pi/surrortg-sdk/setup.py") as f:
        for line in f.readlines():
            if line.startswith('    version="'):
                sdk_version = line.replace('    version="', "").rstrip('",\n')
                break

    click.echo(f"Image version:\t{image_version}")
    click.echo(f"SDK version:\t{sdk_version}")


# Allows listing Commands in order of appearance, instead of alphabetical order
# https://github.com/pallets/click/issues/513
class NaturalOrderGroup(click.Group):
    def list_commands(self, ctx):
        return self.commands.keys()


@click.group(
    cls=NaturalOrderGroup,
    help=(
        "A command line control for SurroRTG SDK, "
        "Streamer and Watcher stream"
    ),
    context_settings=dict(help_option_names=["-h", "--help"]),
    invoke_without_command=True,
)
@click.option(
    "-v", "--version", is_flag=True, help="Show image and SDK versions"
)
def cli(version):
    if version:
        echo_versions()

    # Show help with -h/--help or when empty
    # 'invoke_without_command=True' is required for --version,
    # so this check is required to not invoke help every time
    if (
        len(sys.argv) == 1
        or len(sys.argv) == 2
        and sys.argv[1] in {"--help", "-h"}
    ):
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()


@cli.command(help="Set or show the current game path.")
@click.argument("path", default="", type=click.Path())
def path(path):
    if path == "":
        get_path()
    else:
        set_path(path)


@cli.command(help="Set or show the current game engine token.")
@click.argument("token", default="", type=str)
def token(token):
    if token == "":
        get_token()
    else:
        set_token(token)


@cli.command(
    help="Show logs for the specified service, defaults to 'controller'"
)
@click.argument(
    "target",
    default="controller",
    type=click.Choice(
        ["controller", "streamer", "watcherstream"], case_sensitive=False
    ),
)
@click.option("-f", "--follow", is_flag=True, help="Follows the logs")
def logs(target, follow):
    f = "--follow " if follow else ""
    e = " -e" if not follow else ""
    command(f"sudo journalctl {f}--unit {TARGETS[target]}{e}")


@cli.command(
    help="Restart all services or the specified service, defaults to 'all'."
)
@click.argument(
    "target",
    default="all",
    type=click.Choice(
        ["all", "controller", "streamer", "watcherstream"],
        case_sensitive=False,
    ),
)
def restart(target):
    command(f"sudo systemctl restart {TARGETS[target]}")


@cli.command(
    help="Start all services or the specified service, defaults to 'all'."
)
@click.argument(
    "target",
    default="all",
    type=click.Choice(
        ["all", "controller", "streamer", "watcherstream"],
        case_sensitive=False,
    ),
)
def start(target):
    command(f"sudo systemctl start {TARGETS[target]}")


@cli.command(
    help="Stop all services or the specified service, defaults to 'all'."
)
@click.argument(
    "target",
    default="all",
    type=click.Choice(
        ["all", "controller", "streamer", "watcherstream"],
        case_sensitive=False,
    ),
)
def stop(target):
    command(f"sudo systemctl stop {TARGETS[target]}")


@cli.command(
    help=(
        "Show status of all services or the specified service, "
        "defaults to 'all'."
    )
)
@click.argument(
    "target",
    default="all",
    type=click.Choice(
        ["all", "controller", "streamer", "watcherstream"],
        case_sensitive=False,
    ),
)
def status(target):
    command(f"sudo systemctl status {TARGETS[target]}")


if __name__ == "__main__":
    cli()
