import os
import datetime
import tempfile
import shutil

import click
import PyPDF2

from src.utils.diary_entry_pdf import write_diary_entry_pdf


@click.group()
def cli():
    pass


def merge_pdfs(paths, output):
    pdf_writer = PyPDF2.PdfWriter()

    for path in paths:
        pdf_reader = PyPDF2.PdfReader(path)
        for page in range(len(pdf_reader.pages)):
            # Add each page to the writer object
            pdf_writer.add_page(pdf_reader.pages[page])

    # Write out the merged PDF
    with open(output, 'wb') as out:
        pdf_writer.write(out)

class DatedFile:

    def __init__(self, path, date_created, date_last_modified, order_by):
        self.path = path
        self.date_created = datetime.datetime.fromtimestamp(date_created)
        self.date_last_modified = datetime.datetime.fromtimestamp(date_last_modified)
        self.date = (
            self.date_created if order_by == "date-created" else self.date_last_modified
        )

    @classmethod
    def from_file(cls, realpath, order_by):
        return cls(
            path=os.path.basename(realpath),
            date_created=os.path.getctime(realpath),
            date_last_modified=os.path.getmtime(realpath),
            order_by=order_by,
        )


def perform_export(dirpath, outpath, date_last_export, order_by, reversed):
    files = list(filter(lambda x: x.lower().endswith(".md"), os.listdir(dirpath)))
    fullpaths = [os.path.join(dirpath, f) for f in files]
    print(f'Found {len(fullpaths)} total entries in directory "{dirpath}"')
    dated_file_objects = [DatedFile.from_file(f, order_by) for f in fullpaths]
    relevant_file_objects = (
        [fo for fo in dated_file_objects if fo.date.date() > date_last_export.date()]
        if date_last_export is not None
        else dated_file_objects
    )
    if date_last_export is not None:
        print(
            f"found {len(relevant_file_objects)} after date {date_last_export.date().isoformat()}"
        )
    print(
        f'Generating, stitching, and saving {len(relevant_file_objects)} files to "{outpath}"'
    )
    sorted_date_objects = sorted(
        relevant_file_objects, key=lambda x: x.date, reverse=reversed
    )

    with tempfile.TemporaryDirectory() as tempdir:

        for i, obj in enumerate(sorted_date_objects):
            write_diary_entry_pdf(obj.path, tempdir, f"{i}.pdf")
        filepaths = [os.path.join(tempdir, f"{i}.pdf") for i in range(len(sorted_date_objects))]
        merge_pdfs(filepaths, outpath)


@cli.command()
@click.argument("dirpath", type=str, required=False, default=None)
@click.option(
    "--order-by",
    type=click.Choice(
        [
            "date-created",
            "date-last-modified",
        ]
    ),
    required=False,
    default="date-created",
)
@click.option("--out", "-o", type=str, required=False, default=None)
@click.option("--reversed", is_flag=True, default=False)
def export(dirpath, order_by, out, reversed):
    if dirpath is None:
        dirpath = os.getcwd()
    if "~" in dirpath:
        dirpath = dirpath.replace("~", os.path.expanduser("~"))
    realpath = (
        os.path.normpath(os.path.join(os.getcwd(), dirpath))
        if not os.path.isabs(dirpath)
        else os.path.normpath(dirpath)
    )
    if out is None:
        out = os.path.join(realpath, "export.pdf")
    out = (
        os.path.normpath((os.path.join(realpath, out)))
        if not os.path.isabs(out)
        else os.path.normpath(out)
    )
    filepath = os.path.join(realpath, ".last-export.txt")
    date_last_export = None
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            date_last_export = datetime.datetime.strptime(
                f.read(), "%Y-%m-%d %H:%M:%S.%f"
            )

    perform_export(realpath, out, date_last_export, order_by, reversed)

    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(datetime.datetime.now()))


@cli.command()
@click.argument("dirpath", type=str, required=False, default=None)
def reset_date_last_export(dirpath):
    if dirpath is None:
        dirpath = os.getcwd()
    if "~" in dirpath:
        dirpath = dirpath.replace("~", os.path.expanduser("~"))
    realpath = (
        os.path.normpath(os.path.join(os.getcwd(), dirpath))
        if not os.path.isabs(dirpath)
        else os.path.normpath(dirpath)
    )
    filepath = os.path.join(realpath, ".last-export.txt")
    if os.path.exists(filepath):
        os.remove(filepath)


# Future feature, not part of MVP
# def set_date_last_export():
#     pass


if __name__ == "__main__":
    cli()
