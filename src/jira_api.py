import os
import re

import requests
from requests.auth import HTTPBasicAuth

BASE = os.environ["INPUT_JIRA_SERVER"]
PROJECT = os.environ["INPUT_JIRA_PROJECT"]
USER = os.environ["INPUT_JIRA_USER"]
TOKEN = os.environ["INPUT_JIRA_TOKEN"]

base_url = f"{BASE}/rest/api/3/"
project_path = f"project/{PROJECT}"
auth = HTTPBasicAuth(USER, TOKEN)


def get(endpoint, params=None):
    return requests.get(
        base_url + project_path + "/" + endpoint, params=params, auth=auth
    ).json()


def post(endpoint, body):
    return requests.post(base_url + endpoint, json=body, auth=auth)


def put(endpoint, body):
    return requests.put(base_url + endpoint, json=body, auth=auth)


def get_project_id():
    resp = requests.get(
        f"{base_url}project/{PROJECT}",
        auth=auth,
    )
    resp.raise_for_status()
    return resp.json()["id"]

def get_project_versions():
    project_id = get_project_id()
    resp = requests.get(
        f"{base_url}project/{project_id}/versions",
        auth=auth,
    )
    resp.raise_for_status()
    return resp.json()

def get_or_create_release(release_name):
    versions = get_project_versions()

    matches = [v for v in versions if v.get("name") == release_name]

    if not matches:
        resp = post(
            "version",
            {"name": release_name, "projectId": get_project_id()},
        )
        created = resp.json()

        if "errorMessages" in created or "errors" in created:
            raise Exception(
                f"Jira API error while creating version '{release_name}': {created}"
            )

        return created

    if len(matches) > 1:
        raise Exception(f"Found multiple releases with the same name: {release_name}")

    return matches[0]


def is_valid_issue_key(issue):
    """Return True only if issue matches the expected PROJECT-<non-zero-number> format."""
    if not issue:
        return False
    return bool(re.fullmatch(rf"{re.escape(PROJECT)}-[1-9][0-9]*", issue))


def add_release_to_issue(release_name, issue):
    if not is_valid_issue_key(issue):
        print(f"Warning: skipping invalid or placeholder issue key '{issue}'")
        return False
    response = put(
        f"issue/{issue}",
        {"update": {"fixVersions": [{"add": {"name": release_name}}]}},
    )
    response.raise_for_status()
    return response.status_code == 204
