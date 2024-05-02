import os
import datetime

import markdown
import pdfkit


def suffix(day):
    """Return the suffix for the day in the month."""
    if 4 <= day <= 20 or 24 <= day <= 30:
        return "th"
    else:
        return ["st", "nd", "rd"][day % 10 - 1]


def format_date(d):
    """Format datetime object to 'Month day, year' format with correct suffix for day."""
    day = d.day
    month = d.strftime("%B")
    year = d.year
    return f"{month} {day}{suffix(day)}, {year}"


DIARY_ENTRY_TEMPLATE = """
<div style=\"width:100%; display: flex; flex-direction: column;\">

<div style="display:flex;flex-direction:row;align-items:center;">
    <h1 style="display:inline">{TITLE}</h1>
    <div style="display:flex; flex-direction:column;margin-left:auto;">
        <div>
        Created: {CREATED}
        </div>
        <div>
        Last Modified: {LAST_MODIFIED}
        </div>
    </div>
</div>

<div style="width: 100%">
    {CONTENT}
<div>

</div>
"""


def write_diary_entry_pdf(fullpath, outdir, basename):
    with open(fullpath, "r", encoding="utf-8") as f:
        content = f.read()
        title = os.path.basename(fullpath)[: -len(".md")]
        content_html = markdown.markdown(content)
        filled_template = DIARY_ENTRY_TEMPLATE.format(
            **{
                "TITLE": title,
                "CONTENT": content_html,
                "CREATED": format_date(
                    datetime.datetime.fromtimestamp(os.path.getctime(fullpath))
                ),
                "LAST_MODIFIED": format_date(
                    datetime.datetime.fromtimestamp(os.path.getmtime(fullpath))
                ),
            }
        )
        pdfkit.from_string(filled_template, os.path.join(outdir, basename))