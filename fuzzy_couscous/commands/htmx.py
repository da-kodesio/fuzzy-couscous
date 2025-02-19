from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx
import typer
from fuzzy_couscous.utils import RICH_ERROR_MARKER
from fuzzy_couscous.utils import RICH_INFO_MARKER
from fuzzy_couscous.utils import RICH_SUCCESS_MARKER
from rich import print as rich_print
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn


def _get_web_types_content(version: str) -> str | None:
    response = httpx.get(
        f"https://api.github.com/repos/bigskysoftware/htmx/contents/editors/jetbrains/htmx.web-types.json?ref=v{version}"
    )
    content = response.json()["content"]
    decoded_bytes = base64.b64decode(content)
    return decoded_bytes.decode("utf-8")


def _get_latest_tag() -> str:
    response = httpx.get(
        "https://api.github.com/repos/bigskysoftware/htmx/releases/latest"
    )
    return response.json()["tag_name"][1:]


def _get_download_url(version: str, extension: str | None = None) -> str:
    base_url = f"https://unpkg.com/htmx.org@{version}/dist/"
    if extension:
        return f"{base_url}/ext/{extension}.js"
    return f"{base_url}htmx.min.js"


def htmx(
    version: str = typer.Argument("latest", help="The version of htmx to download."),
    output_file: str = typer.Option(
        "htmx.min.js",
        "-f",
        "--output-file",
        help="The filename for the htmx download.",
    ),
    extension: str = typer.Option(
        None, "-e", "--extension", help="The name of the extension to download."
    ),
    output_dir: Path = typer.Option(
        Path,
        "-d",
        "--output-dir",
        file_okay=False,
        dir_okay=True,
        writable=True,
        exists=True,
        help="The directory to write the downloaded file to.",
    ),
    web_types: bool = typer.Option(
        False, "-w", "--web-types", help="Download the web-types file."
    ),
):
    """Download the htmx javascript library or one of its extension if specified."""

    latest_version = _get_latest_tag()
    version = version if version != "latest" else latest_version
    url = _get_download_url(version=version, extension=extension)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            msg = f"htmx version {version}"
            if extension:
                msg = f"{extension} extension for {msg}"
            progress.add_task(f"Downloading {msg} :arrow_down:", total=None)
            response = httpx.get(url)
    except httpx.ConnectError as e:
        typer.echo(f"{RICH_ERROR_MARKER} Could not connect to {url}")
        raise typer.Abort() from e

    if response.status_code == 404:
        msg = f"Could not find {version} version of htmx."
        if extension:
            msg = f"Could not find {extension} extension for {version} version of htmx."
        rich_print(f"{RICH_ERROR_MARKER} {msg}")
        raise typer.Abort()

    if response.status_code != 200:
        rich_print(f"{RICH_ERROR_MARKER} Something went wrong :sad_face: .")
        raise typer.Abort()

    # write file to disk
    filename = f"{extension}.js" if extension else output_file
    filepath = output_dir / filename
    filepath.write_text(response.content.decode("utf-8"))

    rich_print(
        f"{RICH_SUCCESS_MARKER} File downloaded successfully to {filepath.name}."
        f"\n{RICH_INFO_MARKER} htmx version: {version}"
    )
    if version != latest_version:
        rich_print(
            f"{RICH_INFO_MARKER} The latest version available of htmx version is {latest_version}"
        )

    if not web_types:
        return None

    try:
        web_types_content = _get_web_types_content(version)
    except (httpx.ConnectError, json.JSONDecodeError) as e:
        rich_print(f"{RICH_ERROR_MARKER} Could not download web-types file.")
        raise typer.Exit() from e

    json_file = output_dir / "htmx.web-types.json"

    json_file.write_text(web_types_content)
    rich_print(f"{RICH_INFO_MARKER} Web-types file downloaded to {json_file.name}.")
