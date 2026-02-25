import ai
import argparse
import asyncio
import logging
from pathlib import Path

from pydantic import BaseModel
from scripts.extract import extract
import models

DATA_DIR = Path(__file__).resolve().parent / "data"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Argument parsing so that we can run either one file or all files in the data directory.
    parser = argparse.ArgumentParser(description="Extract product data from HTML.")
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="HTML filename (e.g. nike.html). If omitted, process all .html files in data/.",
    )
    args = parser.parse_args()

    async def run():
        # If a file is provided, process only that file.
        if args.file is not None:
            # Grab the path to the file
            path = Path(args.file)
            # If the path is not absolute, make it absolute by appending the name of the file to the data directory (data folder)
            if not path.is_absolute():
                path = DATA_DIR / path.name
            # If the path does not exist, raise an error.
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            paths = [path]
         # If no file is provided, process all files in the data directory.
        else:
            # Get all the html files in the data directory and sort them by name.
            paths = sorted(DATA_DIR.glob("*.html"))
            # If no files are found, log a warning and return.
            if not paths:
                logging.warning("No .html files found in %s", DATA_DIR)
                return

        # Process each file in the paths list.
        for p in paths:
            # Log the name of the file being processed.
            logging.info("Processing %s", p.name)
            # Read the content of the file.
            content = p.read_text(encoding="utf-8", errors="replace")
            # Run the extract function on the file which parses and saves the data to the data_out.csv file.
            result = await extract(
                models.ExtractRequest(html_content=content),
                source_filename=p.name,
            )
            logging.info("Result: %s", result)
    
    asyncio.run(run())