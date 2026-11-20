# Unpublishing a page

How pages come down from the area sites, routinely or urgently. Claude's `ver-publish` skill follows this same process; this document is the reference for people.

## Who can ask

Anyone on staff can ask to take a page down: the page's owner (listed in its `project.json`), an area lead, a web admin, or someone who spots a problem. Ask through Claude ("unpublish the Chocó school map from Education") or tell a web admin directly.

## Which track

| | Routine | Urgent |
|---|---|---|
| **When** | Outdated, replaced, no longer needed | The page exposes something that must not be public: personal data (names tied to data, contact details, ID numbers, small groups that identify people), confidential information, or content that could harm someone |
| **Who approves** | The area lead, through the normal PR review | A web admin merges immediately, without waiting for approval |
| **How fast** | Whenever it's reviewed | Within the hour |

When in doubt, treat it as urgent. Taking a page down early costs little; leaving exposed data up does not.

## What removal does

Merging a PR that deletes `<area>/<slug>/` republishes that area. The publish workflow rebuilds the area's `site-*` repo from scratch as a single commit, so the page's files are removed from GitHub entirely, not only from the live site. The full record stays in `ver-sites`, which is private.

## Routine removal

1. Open a PR that deletes the project folder, titled `Unpublish: <title> (<Area>)`, with the address, owner, requester and reason in the description. Claude does this for you; by hand:
   ```bash
   git switch main && git pull --ff-only
   git switch -c unpublish/<area>-<slug>
   git rm -r <area>/<slug>
   git commit -m "Unpublish <area>/<slug>"
   git push -u origin HEAD
   gh pr create --base main --fill
   ```
2. The area lead approves and merges, checking with the owner first if someone else asked.
3. The page returns a 404 a few minutes after the merge.

## Urgent removal

**1. Open the PR.** Title it `URGENT unpublish: <title> (<Area>)`. In the description, say what kind of problem it is ("student counts below 5 per school"); don't copy the sensitive data into the PR.

**2. A web admin merges it right away.** First confirm the PR only deletes that one folder:
```bash
gh pr diff <number> --name-only    # only paths inside <area>/<slug>/
gh pr merge <number> --squash --delete-branch --admin
```

**3. Confirm it's gone.**
```bash
gh run watch                                                     # the "Publish areas" run must succeed
curl -sI https://<area>.velezreyesmas.org/<slug>/ | head -1      # expect HTTP/2 404
```
GitHub Pages can take a few minutes to update. If it still returns 200 after 10 minutes, check that the publish run succeeded, then check the latest Pages build in the `site-*` repo.

**4. Remove it from Google, if it was indexed.** Search `site:<area>.velezreyesmas.org/<slug>`. If it appears, use Google Search Console → **Removals** → **New request** for the page's address. Search Console needs `velezreyesmas.org` verified as a domain property, a one-time setup done with a TXT record in Cloudflare. Do that setup now rather than during an incident.

**5. Decide whether the private history also needs cleaning.** The page's content remains in `ver-sites` history and in its pull requests, which only organization members can see. For most cases that's acceptable. If the data is highly sensitive (for example, about minors), a web admin can rewrite `ver-sites` history to remove it and ask GitHub Support to purge cached copies and pull request diffs. That's a deliberate, rare step; plan it rather than improvising during the incident.

**6. Record what happened.** Open a ticket in the TAP Jira project with: the page, what was exposed, how long it was live, who removed it and when, and anything to change so it doesn't happen again. Tell the page's owner and the area lead.

## Copies we can't control

Once something has been public, assume copies may exist: in browser caches, in downloads or screenshots, or in web archives. Removal limits further exposure; it can't undo what's already been copied. That's why the review before publishing matters most.
