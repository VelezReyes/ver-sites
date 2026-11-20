# ver-sites

Public web pages for every VélezReyes+ area. Each area has its own address:

| Area | Address |
|---|---|
| Education | `education.velezreyesmas.org` |
| MEL | `mel.velezreyesmas.org` |
| Leadership | `leadership.velezreyesmas.org` |
| Public Leadership and Innovation | `public-leadership.velezreyesmas.org` |
| Comms and Admin | `comms-admin.velezreyesmas.org` |
| Democracia+ | `democracia.velezreyesmas.org` |
| Aprendo+ | `aprendo.velezreyesmas.org` |

Each project is a folder inside its area, and its folder name becomes its address: `education/becatech/` is published at `education.velezreyesmas.org/becatech/`.

> **Everything here is public.** Anyone on the internet can open these pages, including ones hidden from the project list. Never publish names, emails, ID numbers, phone numbers or any other personal data, even about a single person. Pages with sensitive information belong in the restricted system, not here.

## Publish a page

1. Create a folder in your area: `<area>/<project-name>/`.
   - Use lowercase letters, numbers and hyphens only: `scholar-outcomes`, not `Scholar Outcomes` or `resultados-becas-2026 (final)`. No accents.
2. Put the page in it as `index.html`. Images and other files the page uses go in the same folder.
3. Optionally add a `project.json` to control how the project appears on the area's list:
   ```json
   {
     "title": "Scholar outcomes dashboard",
     "description": "Graduation and employment rates for past cohorts.",
     "updated": "2026-11-19",
     "owner": "name@velezreyesmas.org",
     "hidden": false
   }
   ```
   Without it, the list uses the page's `<title>` and `<meta name="description">`, and the date of the last change.
4. Open a pull request. Automatic checks run first, then one of your area's leads approves it.
5. Once merged, the page is live in a couple of minutes.

Starting from scratch? Copy `_template/project-starter/`. It already uses the brand fonts, colors and header.

## Update or unpublish

- **Update:** change the files in the project folder and open a pull request.
- **Unpublish:** delete the project folder in a pull request. It disappears from the site when merged.
- **Hide from the list:** set `"hidden": true` in `project.json`. The page stays reachable by its address; it just isn't listed.

## Shared styles

Every area site serves the brand stylesheet at `/_assets/ver.css` and the header image at `/_assets/header.png`. Link them from your page, or make the page fully self-contained, which is how pages exported from Claude usually come out. Both work.

## What the automatic checks catch

| Check | Result |
|---|---|
| Folder or file name with capitals, spaces or accents | Blocks the merge |
| Project folder without `index.html` | Blocks the merge |
| Files outside an area/project folder | Blocks the merge |
| File over 25 MB | Blocks the merge |
| An email address (other than `@velezreyesmas.org`) | Blocks the merge |
| A long number that could be an ID or phone number | Warning for the reviewer |
| A raw data file (`.csv`, `.xlsx`, `.json`) | Warning for the reviewer |

The checks catch common mistakes, not every kind of personal data. The reviewer is still responsible for reading the page before approving it.

## For admins

Setup, the publisher app, Cloudflare DNS and adding new areas are covered in [docs/SETUP.md](docs/SETUP.md).
