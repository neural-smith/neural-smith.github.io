# Neural Smith — GitHub Pages site

A small, zero-JavaScript Jekyll catalog for the Neural Smith open-source tools organization.

## Deploy

1. Create a **public** repository named `neural-smith.github.io` under the `neural-smith` organization.
2. Copy the **contents** of this folder to the repository root, commit, and push to `main`.
3. In **Settings → Pages**, choose **Deploy from a branch** and select `main` / `/(root)`.
4. The site will be published at <https://neural-smith.github.io/>.

This uses GitHub Pages' built-in Jekyll processing, not a custom GitHub Actions workflow. The organization homepage is distinct from the `print-creator` project's own Pages site, so it won't interfere with the signed Flatpak repository or web application hosted under `/print-creator/`.

## Add another tool

Append one item to `_data/tools.yml`:

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

Jekyll automatically creates an additional tool card. No HTML edits required.

## Branding

The **official Neural Smith GitHub organization avatar** serves as the navbar image, large header/hero image, favicon, Apple touch icon and social preview. Its URL lives in one place: `_config.yml` under `logo`. This references GitHub's image CDN directly, so it tracks changes to the organization's avatar and doesn't require an additional logo file or image processing. The trade-off is that the logo requires access to GitHub's avatar CDN. For fully self-hosted assets, save the logo under `assets/images/` and update `logo` to that local path (and adjust URL handling if needed).

The site uses the Catppuccin Mocha / Latte palette with Sapphire accents, automatically following the operating system's light/dark preference. No cookies, tracking, external fonts or JavaScript are used.

## Local preview

With Ruby and Bundler installed:

```bash
bundle install
bundle exec jekyll serve --livereload
```

Open <http://localhost:4000/>. GitHub Pages handles Jekyll builds after pushing to the configured branch.

## Structure

```text
_config.yml             Site identity, favicon and avatar source
_data/tools.yml         Single list of apps
_layouts/default.html   Shared HTML shell and navigation
index.html              Homepage built from the data list
assets/css/style.css    Responsive CSS with automatic light/dark theme
Gemfile                 Optional local Jekyll dependencies
```
