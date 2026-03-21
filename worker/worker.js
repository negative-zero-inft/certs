const PAGES = "https://negative-zero-inft.github.io/certs";
const REPO  = "negative-zero-inft/certs";
const BRANCH = "svg";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/^\//, "").trim();

    if (!path || path === "index.html") {
      return fetch(`${PAGES}/${path}`);
    }

    const target = `https://raw.githubusercontent.com/${REPO}/refs/heads/${BRANCH}/${path}.svg`;
    return Response.redirect(target, 302);
  }
};
