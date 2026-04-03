import markdown, sys
from pathlib import Path

name = sys.argv[1]
md_text = Path(f"{name}.md").read_text()
html_body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

html = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 2cm 2.5cm;
  @bottom-center {{ content: counter(page); font-size: 9pt; color: #8c96ad; }} }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
  font-size: 11pt; line-height: 1.6; color: #334059; }}
h1 {{ font-size: 20pt; color: #0065DC; border-bottom: 3px solid #0065DC; padding-bottom: 8px; margin-top: 0; }}
h2 {{ font-size: 15pt; color: #004494; margin-top: 28px; border-bottom: 1px solid #eaeaef; padding-bottom: 4px; }}
h3 {{ font-size: 12pt; color: #334059; margin-top: 20px; }}
h4 {{ font-size: 11pt; color: #334059; margin-top: 16px; }}
table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 10pt; }}
th {{ background-color: #f6f6f6; text-align: left; padding: 8px 10px; border: 1px solid #eaeaef; font-weight: 600; }}
td {{ padding: 6px 10px; border: 1px solid #eaeaef; vertical-align: top; }}
tr:nth-child(even) td {{ background-color: #fafafa; }}
code {{ font-family: Consolas, monospace; font-size: 9.5pt; background: #f6f6f6; padding: 1px 4px; border-radius: 3px; color: #004494; }}
pre {{ background: #f6f6f6; border: 1px solid #eaeaef; border-radius: 4px; padding: 12px 16px; font-size: 9pt; line-height: 1.5; }}
pre code {{ background: none; padding: 0; color: #334059; }}
strong {{ color: #004494; }}
hr {{ border: none; border-top: 1px solid #eaeaef; margin: 24px 0; }}
p {{ margin: 8px 0; }} ul, ol {{ margin: 8px 0; padding-left: 24px; }} li {{ margin: 4px 0; }}
</style></head><body>{html_body}</body></html>"""

Path(f"{name}.html").write_text(html)
import subprocess
subprocess.run(["weasyprint", f"{name}.html", f"{name}.pdf"], check=True)
Path(f"{name}.html").unlink()
print(f"Created {name}.pdf")
