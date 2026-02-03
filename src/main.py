import os
import re
from pprint import pprint

from jira_api import add_release_to_issue, get_or_create_release
from notes_parser import extract_changes, extract_issue_id


def extract_version_from_tag(tag):
    """
    Extract version number from tag pattern 'release/prod/[version]-RC.[number]'.
    Example: 'release/prod/1.1.0-RC.12' -> '1.1.0'
    If pattern doesn't match, returns the original tag.
    """
    match = re.match(r'release/prod/(.+?)-RC\.\d+', tag)
    if match:
        return match.group(1)
    return tag


release_name = extract_version_from_tag(os.environ["GITHUB_REF_NAME"])
release = get_or_create_release(release_name)
print("JIRA Release:")
pprint(release)

changes = extract_changes()
print("Release Issues:")
pprint(changes)

for change in changes:
    issue_id = extract_issue_id(change["title"])
    if not issue_id:
        print("No issue id:", change["title"])
        continue
    print("Updating", issue_id)
    add_release_to_issue(release_name, issue_id)
