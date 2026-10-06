<script>
// Apps Script adapter: serves data/*.txt through google.script.run and maps the page's user/db calls
// (Brand POC access) onto the web app's signed-in Google account.
(() => {
  const run = (fn, ...a) => new Promise((ok, no) => google.script.run.withSuccessHandler(ok).withFailureHandler(no)[fn](...a));
  const text = async name => {
    const first = await run("getData", name, 0);
    const rest = await Promise.all(Array.from({ length: first.n - 1 }, (_, i) => run("getData", name, i + 1)));
    return first.s + rest.map(p => p.s).join("");
  };
  const nativeFetch = window.fetch.bind(window);
  window.fetch = (url, opt) => {
    const m = typeof url === "string" && url.match(/^data\/([A-Za-z0-9_]+)\.txt$/);
    if (!m) return nativeFetch(url, opt);
    return text(m[1]).then(t => new Response(t), e => new Response(String(e && e.message || e), { status: 500 }));
  };
  const blank = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==";
  const person = id => ({ id, name: id, avatarUrl: blank });
  let who = null;
  const user = {
    me: async () => (who = who || await run("whoAmI")),
    search: async q => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(q) ? [person(q.toLowerCase())] : [],
    profiles: async ids => Object.fromEntries(ids.map(id => [id, person(id)])),
  };
  const db = {
    doc: () => ({
      get: async () => { const ids = await run("getPocIds"); return { exists: true, data: () => ({ ids }) }; },
      set: async v => { await run("setPocIds", v.ids || []); },
    }),
  };
  window.claude = { use: async n => n === "user" ? user : n === "db" ? db : null };
})();
</script>
