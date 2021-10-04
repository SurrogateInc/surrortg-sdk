import argparse
import asyncio
import functools
import logging
from subprocess import run

from .. import ApiClient, Message, get_config

DEFAULT_CONFIG_PATH = "/etc/srtg/srtg.toml"

APT_PACKAGES = [
    "srtg-streamer",
    "srtg-watcherstream",
    "srtg-ffmpeg",
    "srtg-v4l2loopback-dkms",
]
APT_UNITS = ["srtg", "srtg-watcherstream"]


def wait_for_input():
    if args.wait_for_input and args.local:
        input("Press Enter to continue...")


async def verify_repo_unchanged(msg_func):
    result = run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=args.path,
    )

    has_no_changes = result.returncode == 0 and len(result.stdout) == 0

    await msg_func(f"Repo has no changes: {has_no_changes}", 0.01)

    return has_no_changes


def rollback_git(rev):
    result = run(
        ["git", "reset", "--hard", rev], cwd=args.path
    )  # TODO what about errors here, I guess nothing?
    if result.returncode != 0:
        logging.info("Failed to rollback git")


async def update_controller(git_branch, msg_func):
    await msg_func("Updating controller..", 0.01)
    result = run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        cwd=args.path,
    )
    if result.returncode != 0:
        return False
    old_commit = result.stdout.strip()
    await msg_func(f"Commit before update: {old_commit}", 0.03)
    await msg_func("Stopping controller", 0.03)
    result = run(["systemctl", "stop", args.controller_unit])
    if result.returncode != 0:
        return False
    wait_for_input()
    await msg_func("Retrieving new version..", 0.04)
    updated = run(
        ["git", "fetch", "origin", git_branch], cwd=args.path
    ).returncode
    if updated == 0:
        changed = run(
            ["git", "checkout", f"origin/{git_branch}"], cwd=args.path
        ).returncode
        if changed == 0:
            await msg_func("Fetch successful, restarting..", 0.30)
            run(["systemctl", "start", args.controller_unit])
            await msg_func("Controller updated and started", 0.31)
            return True
    await msg_func(f"Update unsuccessful, rollback to {old_commit}", 1.0)
    rollback_git(old_commit)
    return False


def get_package_version(package):
    result = run(
        ["dpkg-query", "-W", "-f=${Version}", package],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise Exception
    return result.stdout


def rollback_apt(versions):
    run(
        [
            "apt-get",
            "install",
            "-y",
            *(f"{name}={version}" for name, version in versions.items()),
        ]
    )  # TODO what about errors here
    run(["systemctl", "start", APT_UNITS])


async def update_apt_packages(msg_func):
    try:
        versions = dict(
            (pkg, get_package_version(pkg)) for pkg in APT_PACKAGES
        )
    except Exception:
        logging.info("Failed to get package versions")
        return False

    await msg_func(f"Apt package versions: {versions}", 0.33)

    result = run(["apt-get", "update", "-y"])
    if result.returncode != 0:
        logging.info("Failed to update apt cache")
        return False

    result = run(["systemctl", "stop", *APT_UNITS])
    if result.returncode != 0:
        logging.info("Failed to stop streamer units")
        return False

    await msg_func("Stopped streamer, ready to update", 0.45)
    wait_for_input()
    await msg_func("Upgrading apt packages..", 0.45)
    upgraded = run(
        ["apt-get", "install", "--only-upgrade", "-y", *APT_PACKAGES]
    ).returncode
    if upgraded == 0:
        await msg_func("Update successful, starting streamer", 0.95)
        result = run(["systemctl", "start", *APT_UNITS])
        if result.returncode != 0:
            rollback_apt(versions)
            return False
        return True
    else:
        await msg_func(f"Update failed, rolling back to {versions}", 1.00)
        rollback_apt(versions)
        return False


async def run_upgrade(msg_func, branch):
    unchanged = await verify_repo_unchanged(msg_func)
    await msg_func(f"Repo unchanged: {unchanged}", 0.01)
    wait_for_input()

    if unchanged:
        await update_controller(branch, msg_func)
    else:
        await msg_func("Repo has changes, skipping controller update", 0.31)

    await update_apt_packages(msg_func)


async def local_printer(msg, progress=0):
    logging.info(f"[{int(progress * 100)}%] {msg}")
    msg_times.append((progress, time.time()))


async def send_status(api_client, msg, progress=0):
    logging.info(f"[{int(progress * 100)}%] {msg}")
    await api_client.send(
        "updateProgress",
        {"robot": config["device_id"], "progress": progress, "message": msg},
    )


def is_controller_up_to_date(target_branch):
    local = run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        cwd=args.path,
    )

    remote = run(
        ["git", "rev-parse", f"origin/{target_branch}"],
        capture_output=True,
        text=True,
        cwd=args.path,
    )

    if local.returncode != 0 or remote.returncode != 0:
        raise Exception("Failed to get controller revisions")

    if local.stdout == remote.stdout:
        logging.info("Controller is up to date")
        return True
    else:
        logging.info("Controller needs an update")
        return False


def are_apt_packages_up_to_date(packages):
    status = run(["apt-get", "update"])
    if status.returncode != 0:
        raise Exception()
    status = run(
        ["apt-get", "-s", "--no-download", "upgrade", "-V", "--fix-missing"],
        capture_output=True,
        text=True,
    )
    if status.returncode != 0:
        raise Exception()
    apt_output = status.stdout.splitlines()
    return all(
        is_apt_package_up_to_date(package, apt_output) for package in packages
    )


def is_apt_package_up_to_date(package, apt_output):
    result = [i for i in apt_output if package in i]
    if len(result) > 0:
        logging.info(f"Apt package {package} needs update")
        return False
    logging.info(f"Apt package {package} up to date")
    return True


def is_everything_up_to_date(target_branch):
    return is_controller_up_to_date(
        target_branch
    ) and are_apt_packages_up_to_date(APT_PACKAGES)


def restart_self():
    run(["systemctl", "restart", "srtg-updater"])


async def message_handler(raw_msg):
    try:
        msg = Message.from_dict(raw_msg)
    except Exception as e:
        logging.info(f"Malformed updater message {e}")

    logging.info(f"updater msg {msg}")
    if msg.event == "startUpdate":
        branch = msg.payload["branch"]
        if is_everything_up_to_date(branch):
            logging.info("No need to update")
        else:
            logging.info(f"Updating to branch {branch}")
            await run_upgrade(
                functools.partial(send_status, api_client), branch
            )
            logging.info("Update successful!")
            restart_self()
        await api_client.send(
            "updateSuccessful", {"robot": config["device_id"]}
        )
    elif msg.event == "checkForUpdates":
        logging.info("Checking for updates..")
        branch = msg.payload["branch"]
        if is_everything_up_to_date(branch):
            logging.info("Software is up to date!")
        else:
            logging.info("Software is not up to date")
            version = ""
            current = run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=args.path,
            )
            if current.returncode == 0:
                version = current.stdout.splitlines()[0]
            await api_client.send(
                "updateAvailable",
                {"robot": config["device_id"], "currentVersion": version},
            )


if __name__ == "__main__":
    logger = logging.getLogger()
    logging.basicConfig(
        format=("conn-chck-{levelname}: {message:<40} ({filename}:{lineno})"),
        style="{",
        level=logging.INFO,
    )
    parser = argparse.ArgumentParser("surrobot updater")
    parser.add_argument(
        "-p",
        "--path",
        help="path to controller git repo root",
        default="/opt/srtg-python",
    )

    parser.add_argument(
        "-w", "--wait_for_input", dest="wait_for_input", action="store_true"
    )

    parser.add_argument(
        "--controller-unit",
        help="controller systemd unit name",
        default="controller",
    )

    parser.add_argument(
        "-c",
        "--config",
        help="path to the config file",
        default=DEFAULT_CONFIG_PATH,
    )

    parser.add_argument(
        "-l",
        "--local",
        help="run once locally, do not start update service",
        dest="local",
        action="store_true",
    )

    parser.add_argument(
        "--check-only",
        help="just run a check",
        dest="check_only",
        action="store_true",
    )

    parser.add_argument(
        "-b", "--branch", help="branch to change to", default="main"
    )

    args = parser.parse_args()

    loop = asyncio.get_event_loop()

    if args.local:
        import time

        start_time = time.time()
        msg_times = []
        if args.check_only:
            if is_everything_up_to_date(args.branch):
                logging.info("Software is up to date!")
            else:
                logging.info("Software is not up to date")
        else:
            loop.run_until_complete(
                local_printer("Starting a local update..", 0.00)
            )
            loop.run_until_complete(run_upgrade(local_printer, args.branch))
        end_time = time.time()
        run_time = end_time - start_time
        logging.info(f"Total run time {run_time}")
        for logtime in msg_times:
            real = logtime[1] - start_time
            logging.info(
                f"Real vs expected progress: {real / run_time} | {logtime[0]}"
            )
    else:
        config = get_config(args.config)
        ge_config = config["game_engine"]

        api_client = ApiClient(
            config["device_id"],
            ge_config["url"],
            ge_config["id"],
            ge_config["token"],
            message_handler,
        )

        logging.info("Starting updater..")
        logging.info(f"Connecting to {ge_config['url']}")

        loop.run_until_complete(api_client.connect())
        logging.info("Registering updater..")
        loop.run_until_complete(
            api_client.send("registerUpdater", {"robot": config["device_id"]})
        )

        logging.info("Registered updater..")
        loop.run_until_complete(api_client.run())
