// -0 Cert Registry Worker
// KV namespace binding: CERTS (set in wrangler.toml)
//
// Key schema:
//   pending:{repo_path}    → { first_seen, hit_count, last_seen }
//   transition:{repo_path} → { real_id }  (set manually via wrangler CLI with --ttl=1209600)
//
// Issued cert IDs are NOT stored in KV — GitHub raw is the source of truth.

const REPO_RE =
  /^(github\.com|gitlab\.com|codeberg\.org|bitbucket\.org)\/[^/]+\/[^/]+/;
const REPO = "negative-zero-inft/certs";
const BRANCH = "svg";
const PAGES = "https://negative-zero-inft.github.io/certs";

const ID_RE = /^[A-Za-z0-9\-_]{7}$/;
const FONT = "system-ui,-apple-system,'Segoe UI',sans-serif";

function awaitingSVG(repoPath) {
  const label = decodeURIComponent(repoPath);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="420" height="64" viewBox="0 0 420 64">
<defs>
  <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%"   stop-color="#5b21b6"/>
    <stop offset="60%"  stop-color="#7c3aed"/>
    <stop offset="100%" stop-color="#8b5cf6"/>
  </linearGradient>
</defs>
<rect width="420" height="64" fill="url(#g)"/>
<rect width="420" height="64" fill="rgba(30,10,60,0.5)"/>
<text x="20" y="30" font-family="${FONT}" font-size="13" font-weight="700" fill="white">Awaiting -0 Certification</text>
<text x="20" y="48" font-family="${FONT}" font-size="10" fill="rgba(255,255,255,0.55)">${label}</text>
</svg>`;
}

function transitionSVG(repoPath, realId) {
  const label = decodeURIComponent(repoPath);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="420" height="80" viewBox="0 0 420 80">
<defs>
  <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%"   stop-color="#5b21b6"/>
    <stop offset="60%"  stop-color="#7c3aed"/>
    <stop offset="100%" stop-color="#8b5cf6"/>
  </linearGradient>
</defs>
<rect width="420" height="80" fill="url(#g)"/>
<rect width="420" height="80" fill="rgba(30,10,60,0.5)"/>
<text x="20" y="26" font-family="${FONT}" font-size="13" font-weight="700" fill="white">Cert URL has changed</text>
<text x="20" y="44" font-family="${FONT}" font-size="10" fill="rgba(255,255,255,0.75)">Update your embed: cert.neg-zero.com/${realId}</text>
<text x="20" y="60" font-family="${FONT}" font-size="10" fill="rgba(255,255,255,0.45)">${label}</text>
<text x="20" y="74" font-family="${FONT}" font-size="9" fill="rgba(255,200,100,0.8)">Not your project? Contact -0 or you may be blacklisted.</text>
</svg>`;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/^\//, "");

    // Editor passthrough
    if (!path || path === "index.html") {
      return fetch(`https://negative-zero-inft.github.io/certs/${path}`, {
        headers: { host: "negative-zero-inft.github.io" },
        redirect: "manual",
      }).then((r) => {
        // if github redirects, just serve a fresh fetch without custom domain
        if (r.status === 301 || r.status === 302) {
          return fetch(`https://negative-zero-inft.github.io/certs/${path}`, {
            headers: { host: "negative-zero-inft.github.io" },
          });
        }
        return r;
      });
    }

    // Pending list API (used by editor sidebar)
    if (path === "api/pending") {
      const list = await env.CERTS.list({ prefix: "pending:" });
      const items = await Promise.all(
        list.keys.map(async ({ name }) => {
          const val = await env.CERTS.get(name, { type: "json" });
          return { repo: name.replace("pending:", ""), ...val };
        }),
      );
      return new Response(JSON.stringify(items), {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }

    // Issued cert — 7 base64url chars
    if (ID_RE.test(path)) {
      const svgUrl = `https://raw.githubusercontent.com/${REPO}/refs/heads/${BRANCH}/${path}.svg`;
      const upstream = await fetch(svgUrl);
      if (upstream.ok) return Response.redirect(svgUrl, 302);
      return new Response("Cert not found", { status: 404 });
    }

    // Vanity repo URL
    const repoPath = path;
    const transition = await env.CERTS.get(`transition:${repoPath}`, {
      type: "json",
    });
    if (transition) {
      return new Response(transitionSVG(repoPath, transition.real_id), {
        headers: {
          "Content-Type": "image/svg+xml",
          "Cache-Control": "no-cache",
        },
      });
    }

    // Log pending hit
    if (!REPO_RE.test(repoPath))
      return new Response(awaitingSVG(repoPath), {
        headers: {
          "Content-Type": "image/svg+xml",
          "Cache-Control": "no-cache",
        },
      });
    const existing = await env.CERTS.get(`pending:${repoPath}`, {
      type: "json",
    });
    const now = new Date().toISOString();
    await env.CERTS.put(
      `pending:${repoPath}`,
      JSON.stringify({
        first_seen: existing?.first_seen ?? now,
        hit_count: (existing?.hit_count ?? 0) + 1,
        last_seen: now,
      }),
    );

    return new Response(awaitingSVG(repoPath), {
      headers: { "Content-Type": "image/svg+xml", "Cache-Control": "no-cache" },
    });
  },
};
