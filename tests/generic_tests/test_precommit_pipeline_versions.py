import unittest
import yaml
import toml


class BlackFlake8VersionsTest(unittest.TestCase):
    """
    Make sure that pre-commit and bitbucket pipeline library versions are
    kept consistent
    """

    def test_black_version_consistency(self):
        precommit_ver = self.get_precommit_ver("https://github.com/ambv/black")
        pipfile_ver = self.get_pipfile_ver("black")
        self.assertEqual(precommit_ver, pipfile_ver)

    def test_flake8_version_consistency(self):
        precommit_ver = self.get_precommit_ver(
            "https://gitlab.com/pycqa/flake8"
        )
        pipfile_ver = self.get_pipfile_ver("flake8")
        self.assertEqual(precommit_ver, pipfile_ver)

    def test_codespell_version_consistency(self):
        precommit_ver = self.get_precommit_ver(
            "https://github.com/codespell-project/codespell"
        )
        pipfile_ver = self.get_pipfile_ver("codespell")
        self.assertEqual(precommit_ver, pipfile_ver)

    def test_markdownlint_version_consistency(self):
        precommit_ver = self.get_precommit_ver(
            "https://github.com/markdownlint/markdownlint", ignore_prefix="v"
        )
        bitbucket_ver = self.get_bitbucket_ver("markdownlint", separator="-v")
        self.assertEqual(precommit_ver, bitbucket_ver)

    def get_precommit_ver(self, repo_url, ignore_prefix=""):
        ver = None
        with open(".pre-commit-config.yaml", "r") as stream:
            for repo in yaml.safe_load(stream)["repos"]:
                if repo["repo"] == repo_url:
                    ver = repo["rev"]
                    if ignore_prefix:
                        ver = ver.split(ignore_prefix)[1]
                    break
        if ver is None:
            self.fail(
                f"Repo {repo_url} not found from .pre-commit-config.yaml"
            )
        return ver

    def get_bitbucket_ver(self, step_name, separator="=="):
        ver = None
        with open("bitbucket-pipelines.yml", "r") as stream:
            for step in yaml.safe_load(stream)["pipelines"]["default"][0][
                "parallel"
            ]:
                if step["step"]["name"] == step_name:
                    ver = step["step"]["script"][0].split(separator)[1].strip()
                    break
        if ver is None:
            self.fail(
                f"Step name {step_name} not found from bitbucket-pipelines.yml"
            )
        return ver

    def get_pipfile_ver(self, package):
        return toml.load("Pipfile")["dev-packages"][package][2:]
