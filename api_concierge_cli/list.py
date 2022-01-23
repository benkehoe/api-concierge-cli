from itertools import zip_longest
import textwrap
from typing import Iterable, Mapping, Tuple

import click

from .platform import Target


def fill(lines: list, length: int, width: int):
    if len(lines) > length:
        raise ValueError
    lines[:] = [l.ljust(width) for l in lines]
    if len(lines) == length:
        return
    for _ in range(length - len(lines)):
        lines.append(" " * width)


def get_widths(total: int) -> Tuple[int, int, int]:
    total_minus_buffer = total - 2
    name_width = int(total_minus_buffer * 0.5)
    description_width = total_minus_buffer - name_width
    return name_width, description_width


def add_global_list_options(list_command: click.Command):
    # list_command.params.append(click.Option(["--foo"]))
    pass

def list_handler(targets: Iterable[Target], kwargs: Mapping):
    name_width, description_width = get_widths(120)

    name_wrapper = textwrap.TextWrapper(
        width=name_width,
        subsequent_indent="  ",
        break_long_words=True,
        break_on_hyphens=False,
    )
    description_wrapper = textwrap.TextWrapper(width=40)

    for target in targets:
        name = target.get_name()
        description = target.get_description() or ""

        wrapped_name = name_wrapper.wrap(name)
        wrapped_description = description_wrapper.wrap(description)

        num_lines = max(
            len(wrapped_name), len(wrapped_description)
        )
        fill(wrapped_name, num_lines, name_width)
        fill(wrapped_description, num_lines, description_width)

        lines = zip(wrapped_name, wrapped_description)

        for line in lines:
            print(" ".join(line))
