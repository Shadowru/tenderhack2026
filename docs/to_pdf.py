import markdown, sys
from pathlib import Path

name = sys.argv[1]
md_text = Path(f"{name}.md").read_text()
html_body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

html = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<style>
@page {{
  size: A4;
  margin: 1.8cm 1.5cm;
  @bottom-center {{ content: counter(page); font-size: 8pt; color: #8c96ad; }}
}}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
  font-size: 10pt;
  line-height: 1.55;
  color: #334059;
}}
h1 {{
  font-size: 18pt;
  color: #0065DC;
  border-bottom: 3px solid #0065DC;
  padding-bottom: 6px;
  margin-top: 0;
  margin-bottom: 12px;
}}
h2 {{
  font-size: 13pt;
  color: #004494;
  margin-top: 22px;
  margin-bottom: 6px;
  border-bottom: 1px solid #eaeaef;
  padding-bottom: 3px;
}}
h3 {{
  font-size: 11pt;
  color: #334059;
  margin-top: 14px;
  margin-bottom: 4px;
}}
h4 {{
  font-size: 10pt;
  color: #334059;
  margin-top: 10px;
  margin-bottom: 3px;
}}

/* === TABLES === */
table {{
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 8.5pt;
  line-height: 1.4;
  table-layout: fixed;
  word-wrap: break-word;
  overflow-wrap: break-word;
}}
th {{
  background-color: #f0f2f7;
  text-align: left;
  padding: 6px 8px;
  border: 1px solid #d4d8e2;
  font-weight: 600;
  color: #004494;
  font-size: 8pt;
}}
td {{
  padding: 5px 8px;
  border: 1px solid #e0e3eb;
  vertical-align: top;
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}}
tr:nth-child(even) td {{
  background-color: #f9fafb;
}}
/* First column slightly wider for names */
th:first-child, td:first-child {{
  font-weight: 500;
}}

/* === CODE === */
code {{
  font-family: "JetBrains Mono", Consolas, "Courier New", monospace;
  font-size: 8.5pt;
  background: #f0f2f7;
  padding: 1px 3px;
  border-radius: 2px;
  color: #004494;
}}
pre {{
  background: #f0f2f7;
  border: 1px solid #e0e3eb;
  border-radius: 4px;
  padding: 10px 12px;
  font-size: 8pt;
  line-height: 1.45;
  white-space: pre-wrap;
  word-wrap: break-word;
}}
pre code {{
  background: none;
  padding: 0;
  color: #334059;
  font-size: 8pt;
}}

/* === INLINE === */
strong {{ color: #004494; }}
hr {{ border: none; border-top: 1px solid #eaeaef; margin: 18px 0; }}
p {{ margin: 6px 0; }}
ul, ol {{ margin: 6px 0; padding-left: 20px; }}
li {{ margin: 3px 0; }}

/* === PRINT HELPERS === */
h2, h3 {{ page-break-after: avoid; }}
table {{ page-break-inside: auto; }}
tr {{ page-break-inside: avoid; }}
</style></head><body>{html_body}</body></html>"""

Path(f"{name}.html").write_text(html)
import subprocess
subprocess.run(["weasyprint", f"{name}.html", f"{name}.pdf"], check=True)
Path(f"{name}.html").unlink()
print(f"Created {name}.pdf")
