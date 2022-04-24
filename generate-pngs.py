#!/usr/bin/env python3

import shlex
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import namedtuple
from pathlib import Path

import tomli

StyledAttrib = namedtuple("StyledAttrib", ["id", "color_key", "color_value"])
StyledSvg = namedtuple("StyledSvg", ["svg_str", "attrib_str", "file_name"])


class Svg:
    def __init__(self, svg_path):
        # self.svg_path = svg_path
        self.name = svg_path.name
        self.config = self._load_config(svg_path)

        self._get_root(svg_path)

    def _load_config(self, svg_path):
        with (svg_path / "config.toml").open("rb") as f:
            config = tomli.load(f)

        return config

    def _get_root(self, svg_path):
        tree = ET.parse(svg_path / "base.svg")

        self.root = tree.getroot()
        self.doc = [f"# {self.name.capitalize()}"]

    def get_style_combos(self):
        styles = {}
        for style in self.config["style"]:

            attrib_colors = [
                [
                    StyledAttrib(attribute["id"], k, v)
                    for k, v in self.config["palette"][attribute["palette"]].items()
                ]
                for attribute in style["attribute"]
            ]

            styles[style["name"]] = [
                (i, j) for i in attrib_colors[0] for j in attrib_colors[1]
            ]

        return styles

    def update_svg(self, styled_combo):
        """create a list of svg strings to turn into images"""

        file_name = self.config["file_prefix"]
        updated_root = self.root
        attrib_colors = []
        for attrib in styled_combo:

            updated_root = modify_element(
                updated_root,
                self.config["namespace"],
                self.config["attribute"][attrib.id],
                color=attrib.color_value,
            )
            attrib_colors.append(
                self.config["attribute"][attrib.id]["name"].format(
                    color_key=attrib.color_key
                )
            )

        file_name += "-" + "-".join(attrib_colors) + ".png"
        return StyledSvg(ET.tostring(updated_root), attrib_colors, file_name)


def progress(i, max, postText):
    n_bar = 50  # size of progress bar
    j = i / max
    sys.stdout.write("\x1b[2K\r")
    sys.stdout.write("\r")
    sys.stdout.write(f"[{'=' * int(n_bar * j):{n_bar}s}] {int(100 * j)}%  {postText}")
    sys.stdout.flush()

    # reset cursor when done
    if i == max:
        sys.stdout.write("\x1b[2K\r")


def modify_element(root, namespace, attrib, color) -> ET.Element:

    for e in root.findall(attrib["xpath"].format(namespace=namespace)):
        e.set("style", attrib["style"].format(color_value=color))

    return root


def svg2png(svg_str, dest_dir, verbose=False):

    # TODO: make width and height optional config values
    cmd = f"""
    inkscape \
        --export-type=png \
        --export-filename={dest_dir} \
        --export-width=3840 \
        --export-height=2160 \
        --pipe
    """
    p = subprocess.run(shlex.split(cmd), input=svg_str, capture_output=True)
    if p.returncode != 0:
        print("Error using inkscape....")
        print(p.stdout)


def make_fig_table(figures):
    cols = 3
    row = '<td align="center">{name}<img src="{url}"></td>'
    rows = [row.format(name=k, url=v) for k, v in figures.items()]
    row_groups = [rows[i : (i + cols)] for i in range(0, len(rows), cols)]

    columns = [
        "<tr>\n{rows}\n</tr>".format(rows="\n".join(group)) for group in row_groups
    ]
    table = "\n<table>\n{columns}\n</table>\n".format(columns="\n".join(columns))
    return table

def make_dest_dirs(src):
    dest_dir = Path("pngs") / src.name
    dest_dir.mkdir(parents=True, exist_ok=True)
    doc_dir = Path("docs")
    doc_dir.mkdir(parents=True, exist_ok=True)

    return dest_dir, doc_dir
def main():
    src = Path(sys.argv[1])
    dest_dir,doc_dir = make_dest_dirs(src)

    svg = Svg(src)

    doc = [f"# {svg.name.capitalize()}"]

    styled_svgs = []
    for style, combos in svg.get_style_combos().items():

        doc.append(f"## {style}" + "\n\n")
        doc.append(f"See [here](../../assets/pngs/{svg.name}) for all png's.")

        print(f"Generating png's for style: {style}")

        styled_svgs = [svg.update_svg(combo) for combo in combos]
        figures = {
            ", ".join(
                styled_svg.attrib_str
            ): f"../../assets/pngs/{svg.name}/{styled_svg.file_name}"
            for styled_svg in styled_svgs
        }

        doc.append(make_fig_table(figures))

        for i, styled_svg in enumerate(styled_svgs, 1):
            progress(i, len(combos), " | ".join(styled_svg.attrib_str))
            svg2png(styled_svg.svg_str, dest_dir / styled_svg.file_name)

    with (Path(doc_dir) / f"{src.name}.md").open("w") as f:
        f.write("\n".join(doc))

    print("done.")


if __name__ == "__main__":
    main()
