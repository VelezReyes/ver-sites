# One-time setup

This is for the web admins. It covers everything you do once, plus the short checklist for bringing each new area live. Contributors only need the [README](../README.md).

The GitHub organization is assumed to be `VelezReyes`. If it's different, change `"org"` in `areas.json` and the team names in `.github/CODEOWNERS`.

## 1. The source repo (`ver-sites`)

1. Create the repo `VelezReyes/ver-sites` and push this scaffold to `main`. It can be private: only the published site repos need to be public.
2. Create the teams named in `.github/CODEOWNERS` (or rename them there to match your existing teams). Give each team **Write** access to `ver-sites`.
3. Add a ruleset for `main` (Settings → Rules → Rulesets → New branch ruleset):
   - Target: the default branch.
   - Require a pull request before merging, with 1 approval and **Require review from Code Owners**.
   - Require status checks to pass: add the `validate` check (it appears after the first PR runs).
   - Block force pushes.

## 2. The publisher GitHub App

The publish workflow uses a GitHub App to push into the `site-*` repos. An App is safer than a personal token: it isn't tied to anyone's account, and it can only touch the repos you install it on.

1. Organization settings → Developer settings → GitHub Apps → **New GitHub App**.
   - Name: `ver-sites publisher`. Homepage URL: `https://velezreyesmas.org`.
   - Webhook: uncheck **Active**.
   - Repository permissions: **Contents → Read and write**. Leave everything else at "No access".
   - Where can this app be installed: **Only on this account**.
2. After creating it, note the **App ID** and click **Generate a private key** (a `.pem` file downloads).
3. Install the app on the organization and choose **Only select repositories**. You'll add each `site-*` repo here as you create them (step 5).
4. In `ver-sites` → Settings → Secrets and variables → Actions:
   - Variables tab: `PUBLISHER_APP_ID` = the App ID.
   - Secrets tab: `PUBLISHER_APP_PRIVATE_KEY` = the full contents of the `.pem` file. Then delete the downloaded file.

## 3. Verify the domain on GitHub

This stops anyone outside your organization from pointing one of your subdomains at their own GitHub Pages site (a "subdomain takeover").

1. Organization settings → Pages → **Add a domain** → `velezreyesmas.org`.
2. GitHub shows a TXT record. In Cloudflare → DNS → Records → **Add record**:
   - Type `TXT`, and the Name and Content exactly as GitHub shows them.
3. Back in GitHub, click **Verify**. DNS can take a few minutes to update.

Verifying the parent domain covers its subdomains, so you do this once.

## 4. Cloudflare notes

- Every area record is a **CNAME** pointing to `velezreyes.github.io`, with **Proxy status: DNS only** (grey cloud). GitHub issues each subdomain's HTTPS certificate itself, and it can't do that, or renew it later, while Cloudflare's proxy sits in front.
- If the zone has any **CAA** records, add one allowing `letsencrypt.org`, or GitHub's certificate request will be refused. If there are no CAA records at all, nothing is needed.

## 5. Bring an area live

Repeat this for each area. Education is the example.

1. **Create the site repo.** New repository `VelezReyes/site-education`, **public**, completely empty (no README). Give only the web admins access. Nobody edits it by hand; the workflow overwrites it on every publish.
2. **Let the app push to it.** Organization settings → GitHub Apps → `ver-sites publisher` → Configure → add `site-education` to the selected repositories.
3. **Add the DNS record in Cloudflare.** Type `CNAME`, Name `education`, Target `velezreyes.github.io`, Proxy status **DNS only**.
4. **Turn the area on.** In a PR to `ver-sites`, set `"live": true` for the area in `areas.json`, then merge. The **Publish areas** workflow builds the site and pushes it to `site-education`.
5. **Turn on Pages.** In `site-education` → Settings → Pages:
   - Source: **Deploy from a branch**, branch `main`, folder `/ (root)`.
   - Custom domain should show `education.velezreyesmas.org` (it comes from the `CNAME` file the workflow writes). If it's empty, type it in and save.
   - Wait for the DNS check to pass and the certificate to be issued (usually minutes, sometimes up to an hour), then tick **Enforce HTTPS**.
6. Open `https://education.velezreyesmas.org/`. You should see the area page.

To add a brand-new area later: add it to `areas.json` (with `"live": false`), add a folder for it with a `.gitkeep`, add its line to `CODEOWNERS`, then follow the checklist above.

## Republishing by hand

Actions → **Publish areas** → Run workflow. Enter an area folder name, or `all`. Use this after changing the app's secret, or if a publish failed.

## How publishing decides what to rebuild

| Change merged to `main` | What gets republished |
|---|---|
| Files under one area folder | That area |
| `_template/`, `scripts/` or `areas.json` | Every live area |
| Manual run | The area you name, or all |

Areas with `"live": false` are never published, so you can prepare content for an area before its repo and DNS exist.
