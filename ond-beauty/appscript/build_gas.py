# Builds the Apps Script upload folder: dist_gas/Beauty Pulse/ = dashboard.html (page + adapter) + the data files.
import pathlib, shutil
here = pathlib.Path(__file__).parent; root = here.parent
out = root / "dist_gas" / "Beauty Pulse"
shutil.rmtree(out.parent, ignore_errors=True); out.mkdir(parents=True)
html = (root / "dist" / "ond_beauty_dashboard.html").read_text()
html = html.replace("<title>Beauty Pulse</title>", "<title>Beauty Pulse</title>\n" + (here / "shim.js").read_text(), 1)
(out / "dashboard.html").write_text(html)
for f in sorted((root / "dist" / "data").glob("*.txt")): shutil.copy(f, out / f.name)
print("wrote", out, len(list(out.iterdir())), "files")
