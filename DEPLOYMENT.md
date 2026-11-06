# Deploying neural-smith.github.io

This repository deploys via an explicit GitHub Actions workflow with extended Pages polling.

## Setup

1. Push this source to `neural-smith/neural-smith.github.io` on `main`.
2. In **Settings → Pages**, select **GitHub Actions** as the publishing source. Disable any existing custom deployment workflow to avoid duplicate publishes. Do not select **Deploy from a branch** alongside this workflow.
3. Under **Settings → Environments → github-pages**, permit branch `main` and confirm no unapproved required reviewer is blocking deployment.
4. Check **Actions → Publish organization website** for the build, upload and direct-API deployment jobs.

The deployment job uses GitHub's `github-pages` environment and `pages: write`, `actions: read`, `id-token: write` scoped permissions. No PAT, extra signing key or other secret is required.

## What the timeout actually means

The usual `actions/deploy-pages@v5` action clamps its `timeout` input to **600,000 milliseconds**. This workflow instead directly creates a Pages deployment using GitHub's documented REST API and OIDC token and polls its status for **3,600 seconds**. The job itself allows **75 minutes**.

This changes the client's patience, **not** GitHub Pages' server processing deadlines. If the service-side deployment is stuck or times out, increasing the script timeout will not fix it. The script records the deployment ID and stops on terminal failure. It does not automatically cancel a slow deployment.

## Troubleshooting

```bash
# Check repository Pages configuration and Actions job history.
gh api repos/neural-smith/neural-smith.github.io/pages
gh run list -R neural-smith/neural-smith.github.io --limit 10

# Use the ID printed by the deployment script.
gh api repos/neural-smith/neural-smith.github.io/pages/deployments/DEPLOYMENT_ID
```

Check [GitHub Status](https://www.githubstatus.com/) and any outstanding protection rules. If deployment creation is accepted but status stays `deployment_queued`, that is not a Jekyll build issue. Avoid repeatedly re-running the workflow while another deployment is active.

## Validation

```bash
python3 -m unittest discover -s tests -v
```

The project's Jekyll catalog is still maintained through `_data/tools.yml`.
