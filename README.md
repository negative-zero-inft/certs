# -0 Certs

Certification registry for Negative Zero. Every certified product gets a transparency card embedded in its README.

## How it works

1. Use the [cert editor](https://negative-zero-inft.github.io/certs/) to fill out a product's cert data
2. Download the JSON — filename format: `{base64id}-{product-name}.json`
3. Drop it in `registry/`
4. Push to `main` — GitHub Actions generates the SVG and pushes it to the `svg` branch
5. Embed in any README:

```markdown
![Negative Zero Cert](https://cert.neg-zero.com/YOUR_BASE64_ID)
```

The SVG auto-switches between dark and light based on the viewer's system theme.

## Repo structure

```
registry/          JSON cert files (source of truth)
svg/               Generated SVGs (auto-managed, do not edit manually)
docs/              GH Pages editor
scripts/           SVG generator
worker/            Cloudflare Worker source
.github/workflows/ CI
```

## Branches

| Branch | Purpose                        |
| ------ | ------------------------------ |
| `main` | JSON registry + editor source  |
| `svg`  | Generated SVGs (written by CI) |

## Cert tiers

| Tier        | Meaning                                      |
| ----------- | -------------------------------------------- |
| FULL        | Fully compliant across all CERTAIN criteria  |
| CONDITIONAL | Compliant with approved necessity exceptions |
| FAIL        | Does not meet the standard                   |
