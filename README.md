# Neural Smith — GitHub Pages site

A small, JavaScript-free Jekyll catalog for Neural Smith tools, published at <https://neural-smith.github.io/>.

## Deploy from GitHub Actions

1. Create the public organization repository **`neural-smith/neural-smith.github.io`** and commit this site's files to the `main` branch.
2. Go to **Settings → Pages → Build and deployment → Source → GitHub Actions**. This is essential: *do not* leave **Deploy from a branch** selected, or GitHub may run its auto-generated `pages-build-deployment` workflow as well.
3. In **Settings → Environments → github-pages**, allow deployments from `main`. If there are required reviewers, approve deployment as necessary.
4. Push a commit to `main`, or manually run **Actions → Publish organization website → Run workflow**.

The workflow at `.github/workflows/pages.yml` builds Jekyll with GitHub's Pages tools, uploads `_site` as an artifact, then **creates the Pages deployment directly through the GitHub REST API**. The script at `scripts/deploy_pages.py` monitors the deployment for up to **60 minutes**, with a **75-minute GitHub Actions job limit**.

The default `actions/deploy-pages@v5` action has a **hardcoded 600,000 ms (10-minute) client timeout**; passing `timeout: 3600000` to the action does not increase it. This project deliberately does not use that deployment action. The direct-API script follows the same documented OIDC authentication and Pages deployment/status endpoints, without that client-side cap.

**Limitations:** a longer client-side timeout cannot bypass GitHub Pages' backend timeout, stuck deployment locks, service outages, size limits, or environment approval rules. If the deployment remains `deployment_queued` until a backend failure, inspect [GitHub Status](https://www.githubstatus.com/) and the [repository's Pages settings](https://github.com/neural-smith/neural-smith.github.io/settings/pages). A separate GitHub community report describes similar server-side queueing and a ten-minute service-side limitation. Avoid repeatedly retriggering stuck deployments, which can make a queue worse.

### Permissions and security

The build job has `contents: read` and `pages: read`. The deployment job has `contents: read`, `actions: read` (find artifact), `pages: write` (create deployment) and `id-token: write` (GitHub Actions OIDC). **No personal access token or additional secret is necessary**. Only deploy from protected `main`, not arbitrary pull requests or tags. `concurrency.cancel-in-progress: false` avoids interrupting an active deployment.

### Troubleshooting a queued deployment

Check the last deployment and its environment settings before retrying:

```bash
gh api repos/neural-smith/neural-smith.github.io/pages
gh run list --repo neural-smith/neural-smith.github.io --limit 10
```

If the workflow created a Pages deployment with an ID or commit SHA, inspect its status:

```bash
gh api repos/neural-smith/neural-smith.github.io/pages/deployments/<DEPLOYMENT_ID>
```

If GitHub reports a deployment is stuck, investigate it before starting another one. The workflow does **not automatically cancel** an older deployment after its 60-minute local polling limit, because forced cancellation can leave a locked deployment. GitHub Pages may also experience deployment queue delays independently of this repository.

### Run deployment script tests

```bash
python3 -m unittest discover -s tests -v
```

## Add another tool

Append an item to `_data/tools.yml`:

```yaml
- name: Example Tool
  initials: ET
  category: Developer Tools
  description: A short explanation of what the app does.
  platforms: [Linux, Browser]
  technologies: [Rust, Open source]
  links:
    - text: Download
      url: https://github.com/neural-smith/example-tool/releases
      primary: true
    - text: Source code
      url: https://github.com/neural-smith/example-tool
```

Jekyll automatically creates an additional tool card.

## Branding

The official Neural Smith GitHub avatar is the favicon, navbar image, header image and social preview image. `_config.yml` contains its URL as the single source of truth. The site uses Catppuccin Mocha/Latte with Sapphire accents and automatic light/dark preference. It needs no JavaScript, cookies, analytics or external fonts.

## Local preview

```bash
bundle install
bundle exec jekyll serve --livereload
```

Visit <http://localhost:4000/>.

## Project structure

```text
.github/workflows/pages.yml  Jekyll build + direct Pages API deployment
scripts/deploy_pages.py      Extended Pages deployment status polling
tests/test_deploy_pages.py   Deployment script regression tests
_config.yml                 Site identity and avatar source
_data/tools.yml             Application catalog
_layouts/default.html       Shared HTML shell and navigation
index.html                  Homepage generated from catalog
assets/css/style.css        Responsive light/dark styles
Gemfile                     Jekyll dependencies for local preview
```

This organization homepage does not affect the separate Print Creator Flatpak/web Pages deployment under `/print-creator/`.
