from abc import abstractproperty
from dataclasses import dataclass
from io import StringIO
from itertools import chain
from operator import index
from typing import Any, NamedTuple, SupportsIndex, TypeVar

T = TypeVar("T")


def index_or_default(
    lst: list[T],
    value: SupportsIndex,
    start: int = None,
    end: int = None,
    default: T | None = None,
):
    try:
        return lst.index(value, start, end)
    except ValueError:
        return default


def comment_to_string(comment: str):
    return "" if comment == "" else f"#{comment}"


@dataclass
class Directive:
    key: str
    value: str

    def __init__(self, key: Any, value: Any) -> None:
        self.key = str(key)
        self.value = str(value)


# Should have been a @staticmethod, but that failed because of the self-referencing isinstance check
def directive_from_tuple(tuple_: tuple | Directive):
    if isinstance(tuple_, Directive):
        return tuple_
    return Directive(*tuple_)


@dataclass
class IniFileLine:
    comment: str
    space_between: str

    def __init__(self, comment="", space_between="") -> None:
        self.comment = comment
        self.space_between = space_between

    @abstractproperty
    def pre_comment_text(self) -> str:
        pass

    def to_string(self):
        string = ""
        if (pre_comment_text := self.pre_comment_text) != "":
            string += pre_comment_text

        if self.comment != "":
            if string != "" and self.space_between:
                string += " "
            string += comment_to_string(self.comment)

        return string

    def add_comment(self, _comment: str, add_space_before_comment: bool = True):
        if self.comment != "":
            raise Exception("Comment already set")
        if add_space_before_comment:
            _comment = f" {_comment}"
        self.comment = _comment
        self.space_between = " "


class PreCommentLine(IniFileLine):
    pre_comment_spaces: str

    def __init__(self, comment="", pre_comment_spaces=""):
        super().__init__(comment, space_between=False)
        self.pre_comment_spaces = pre_comment_spaces

    @property
    def pre_comment_text(self):
        return self.comment


@dataclass
class SectionTitleLine(IniFileLine):
    title: str

    def __init__(self, title: str, comment="", space_between=""):
        super().__init__(comment, space_between)
        self.title = title

    @property
    def pre_comment_text(self):
        return f"[{self.title}]"


@dataclass
class SectionLine(IniFileLine):
    directive: Directive | None
    delimiter: str

    def __init__(
        self, directive: str, comment="", space_between="", delimiter: str = "="
    ):
        super().__init__(comment, space_between)
        self.directive = directive
        self.delimiter = delimiter

    @staticmethod
    def from_directive(directive_or_kv: tuple | Directive):
        return SectionLine(directive_from_tuple(directive_or_kv), "")

    @property
    def pre_comment_text(self):
        if self.directive is None:
            return ""

        return f"{self.directive.key}{self.delimiter}{self.directive.value}"


@dataclass
class Section:
    titleLine: SectionTitleLine
    lines: list[SectionLine]

    @property
    def directives(self):
        return (line.directive for line in self.lines if line.directive is not None)

    @property
    def directive_tuples(self):
        return (directive.tuple for directive in self.directives)

    def add_directive(self, directive_or_kv: Directive | tuple[str, str]):
        directive = directive_from_tuple(directive_or_kv)
        self.lines.append(SectionLine(directive, ""))

    def add_if_not_present(self, directive_or_kv: Directive | tuple[str, str]):
        directive = directive_from_tuple(directive_or_kv)
        if directive not in self.directives:
            self.lines.append(SectionLine(directive, ""))

    def add_or_replace(self, directive_or_kv: Directive | tuple[str, str]):
        directive = directive_from_tuple(directive_or_kv)
        self.lines = [
            line
            for line in self.lines
            if line.directive is None or line.directive.key != directive.key
        ]
        self.lines.append(SectionLine(directive, ""))

    def add_all_if_not_present(
        self, directives_or_kvs: list[Directive | tuple[str, str]]
    ):
        for directive_or_kv in directives_or_kvs:
            self.add_if_not_present(directive_or_kv)

    def to_lines(self):
        return [
            self.titleLine.to_string(),
            *(line.to_string() for line in self.lines),
        ]

    @staticmethod
    def from_directives(
        title: str, directives_or_kvs: list[Directive | tuple[str, str]]
    ):
        return Section(
            SectionTitleLine(title),
            [
                SectionLine.from_directive(directive_or_kv)
                for directive_or_kv in directives_or_kvs
            ],
        )


class IniFileParseException(Exception):
    pass


class IniConfig:
    _pre_comments: list[PreCommentLine]
    _sections: list[Section]

    def __init__(self, sections: list[Section] = None):
        self._pre_comments = []
        if sections is None:
            sections = []
        self._sections = sections

    def sections_by_title(self, title: str):
        return (
            section for section in self._sections if section.titleLine.title == title
        )

    def single_section_by_title(self, title: str):
        sections = self.sections_by_title(title)
        section = next(sections, None)
        if next(sections, None) != None:
            raise ValueError(f"Found multiple sections with title {title}")
        return section

    def sections_by_directive(self, title: str, directive: Directive):
        return (
            section
            for section in self._sections
            if directive in section.directives and section.titleLine.title == title
        )

    def single_section_by_directive(
        self, title: str, directive_or_kv: Directive | tuple[str, str]
    ):
        directive = directive_from_tuple(directive_or_kv)
        sections = self.sections_by_directive(title, directive)
        section = next(sections, None)
        if next(sections, None) != None:
            raise ValueError(f"Found multiple sections with directive {directive}")
        return section

    def add_section(self, section: Section, add_newline_if_not_first: bool = True):
        if len(self._sections) != 0 and add_newline_if_not_first:
            self._sections[-1].lines.append(SectionLine(None, ""))
        self._sections.append(section)

    def to_lines(self):
        return [
            *(pre_comment.to_string() for pre_comment in self._pre_comments),
            *(chain(*(section.to_lines() for section in self._sections))),
        ]

    def to_string(self):
        return "\n".join(self.to_lines()) + "\n"

    def to_string_io(self):
        return StringIO(self.to_string())

    def write(self, file: Any):
        file.write(self.to_string())

    @staticmethod
    def from_section_directives(
        sections: list[tuple[str, list[Directive | tuple[str, str]]]]
    ):
        return IniConfig(
            [
                Section.from_directives(title, directives)
                for title, directives in sections
            ]
        )

    @staticmethod
    def from_lines(lines: list[str]):
        pre_comments = []
        sections = []
        section = None
        for index, line in enumerate(lines):

            def create_error(message):
                return IniFileParseException(
                    f"Error parsing line {index + 1}: {message} \n"
                    + f"{index + 1}: {line}"
                )

            comment_index = index_or_default(line, "#")
            line_has_comment = comment_index != None
            comment = line[comment_index + 1 :] if line_has_comment else ""

            opening_bracket_index = index_or_default(line, "[", 0, comment_index)
            is_title_line = opening_bracket_index != None

            delimiter_index = index_or_default(line, "=", 0, comment_index)
            is_directive_line = delimiter_index != None

            if line_has_comment:
                if is_title_line and opening_bracket_index > comment_index:
                    is_title_line = False
                if is_directive_line and delimiter_index > comment_index:
                    is_directive_line = False

            if is_title_line and is_directive_line:
                delimiter_after_opening_bracket = (
                    delimiter_index > opening_bracket_index
                )
                is_title_line = not delimiter_after_opening_bracket
                is_directive_line = delimiter_after_opening_bracket

            if is_title_line:
                if opening_bracket_index != 0:
                    raise create_error(
                        f"Invalid section title: opening square bracket is not the first character"
                    )

                closing_bracket_index = line.index("]")
                if closing_bracket_index == -1 or (
                    line_has_comment and closing_bracket_index > comment_index
                ):
                    raise create_error(
                        f"Invalid section title: no closing square bracket"
                    )

                space_between_end = comment_index if line_has_comment else len(line)
                space_between = line[closing_bracket_index + 1 : space_between_end]
                if line_has_comment and space_between.strip() != "":
                    raise create_error(
                        f"Invalid section title: non-space characters between closing square bracket and comment"
                    )

                title = line[1:closing_bracket_index]
                section = Section(SectionTitleLine(title, comment, space_between), [])
                sections.append(section)
            elif is_directive_line:
                spaced_key = line[:delimiter_index]
                spaced_value_end = comment_index if line_has_comment else len(line)
                spaced_value = line[delimiter_index + 1 : spaced_value_end]

                spaced_delimiter_start_offset = next(
                    (i for i, c in enumerate(reversed(spaced_key)) if not c.isspace()),
                    0,
                )
                spaced_delimiter_end_offset = next(
                    (i for i, c in enumerate(spaced_value) if not c.isspace()),
                    len(spaced_value),
                )
                spaced_delimiter_start = delimiter_index - spaced_delimiter_start_offset
                spaced_delimiter_end = delimiter_index + spaced_delimiter_end_offset
                spaced_delimiter = line[
                    spaced_delimiter_start : spaced_delimiter_end + 1
                ]

                key = line[:spaced_delimiter_start]
                if key.isspace():
                    raise create_error(f"Invalid directive: no key")

                if key[0].isspace():
                    raise create_error(f"Invalid directive: key has leading space")

                value_end_offset = next(
                    (
                        i
                        for i, c in enumerate(reversed(spaced_value))
                        if not c.isspace()
                    ),
                    None,
                )

                if value_end_offset == None:
                    raise create_error(f"Invalid directive: no value")

                value_end = spaced_value_end - value_end_offset
                value = line[spaced_delimiter_end + 1 : value_end]
                space_between = line[value_end:spaced_value_end]

                if section is None:
                    raise create_error(
                        f"Invalid directive: directive before section title"
                    )

                directive = Directive(key, value)
                section.lines.append(
                    SectionLine(directive, comment, space_between, spaced_delimiter)
                )
            elif line_has_comment:
                pre_comment_space = line[:comment_index]

                if pre_comment_space.strip() != "":
                    raise create_error(
                        f"Invalid stand-alone comment: non-space characters before comment"
                    )

                if section is None:
                    pre_comments.append(PreCommentLine(comment, pre_comment_space))
                else:
                    section.lines.append(SectionLine(None, comment, pre_comment_space))
            else:
                if line.strip() != "":
                    raise create_error(f"Invalid empty line: non-space characters")

                if section is None:
                    pre_comments.append(PreCommentLine("", line))
                else:
                    section.lines.append(SectionLine(None, "", line))
        return IniConfig(sections)

    @staticmethod
    def from_string(string: str):
        return IniConfig.from_lines(string.splitlines())


if __name__ == "__main__":
    config = IniConfig.from_section_directives(
        [
            (
                "Interface",
                [("Address", "10.200.100.8/24"), ("PrivateKey", "XXXX")],
            )
        ]
    )
    section = Section.from_directives(
        "Peer", [("PublicKey", "YYYY"), ("Endpoint", "demo.wireguard.com:51820")]
    )
    section.add_all_if_not_present(
        [
            ("Endpoint", "demo.wireguard.com:51820"),
            ("AllowedIPs", "0.0.0.0/0"),
        ]
    )
    config.add_section(section)

    peer_section = config.single_section_by_directive("Peer", ("PublicKey", "YYYY"))
    peer_section.add_directive(("AllowedIPs", "fdaa:3160:7c4a::/64"))

    interface_section = config.single_section_by_title("Interface")
    interface_section.titleLine.add_comment("Section title comment")
    interface_section.lines.insert(-1, SectionLine(None, " Comment-only line"))
    interface_section.lines[0].add_comment("Directive comment")

    config_str = config.to_string()
    print("Original:")
    print(config_str)

    out_file = StringIO()
    config.write(out_file)
    assert out_file.getvalue() == config_str

    config_parsed = IniConfig.from_string(config_str)
    config_parsed_str = config_parsed.to_string()
    assert config_parsed_str == config_str
