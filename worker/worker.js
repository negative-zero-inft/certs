// -0 Cert Registry Redirect Worker
// Route: cert.neg-zero.com/:id
// Redirects to the generated SVG on the svg branch of the certs repo

const REPO   = "negative-zero-inft/certs";
const BRANCH = "svg";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const id  = url.pathname.replace(/^\//, "").trim();

    if (!id) {
      return new Response(
        "No cert ID provided. Usage: cert.neg-zero.com/<base64id>",
        { status: 400, headers: { "Content-Type": "text/plain" } }
      );
    }

    const target = `https://raw.githubusercontent.com/${REPO}/refs/heads/${BRANCH}/${id}.svg`;
    return Response.redirect(target, 302);
  }
};
