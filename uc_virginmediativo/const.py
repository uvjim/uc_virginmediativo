""""""
from dataclasses import dataclass
from enum import StrEnum
import ucapi


class CodeTypes(StrEnum):
    """Describe code types."""

    IRCODE = "ircode"
    TELEPORT = "teleport"


@dataclass(frozen=True)
class CodeDefinition:
    """Describe an available code."""

    code: str
    type: CodeTypes
    display_name: str = ""
    repeat: int = 1
    wait: bool = True


# IRCODES not mapped
# "Clear": "Clear"
# "Exit": "Exit"
# "Guide": "Guide",
# "Info": "Info",
# "NUM0": "NUM0",
# "NUM1": "NUM1",
# "NUM2": "NUM2",
# "NUM3": "NUM3",
# "NUM4": "NUM4",
# "NUM5": "NUM5",
# "NUM6": "NUM6",
# "NUM7": "NUM7",
# "NUM8": "NUM8",
# "NUM9": "NUM9",
# "OK": "Select",
# "Play": "Play",
# "Record": "Record",
# "Thumbs Down": "ThumbsDown",
# "Thumbs Up": "ThumpsUp",
# "TV": "LiveTV",
# "Standby": "Standby",

# TELEPORTS not mapped
# "Guide": "GUIDE",
# "Live TV": "LIVETV",

AVAILABLE_COMMANDS: dict[str, CodeDefinition] = {
    "guide": CodeDefinition(code="Guide", display_name="Guide", type=CodeTypes.IRCODE),
    ucapi.media_player.Commands.CHANNEL_DOWN: CodeDefinition(
        code="ChannelDown", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.CHANNEL_UP: CodeDefinition(
        code="ChannelUp", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.CURSOR_DOWN: CodeDefinition(
        code="Down", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.CURSOR_ENTER: CodeDefinition(
        code="Select", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.CURSOR_LEFT: CodeDefinition(
        code="Left", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.CURSOR_RIGHT: CodeDefinition(
        code="Right", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.CURSOR_UP: CodeDefinition(
        code="Up", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.FAST_FORWARD: CodeDefinition(
        code="Forward", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.FUNCTION_BLUE: CodeDefinition(
        code="Action_D", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.FUNCTION_GREEN: CodeDefinition(
        code="Action_B", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.FUNCTION_RED: CodeDefinition(
        code="Action_A", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.FUNCTION_YELLOW: CodeDefinition(
        code="Action_C", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.HOME: CodeDefinition(
        code="TIVO", type=CodeTypes.TELEPORT
    ),
    ucapi.media_player.Commands.MENU: CodeDefinition(
        code="NOWPLAYING", type=CodeTypes.TELEPORT
    ),
    ucapi.media_player.Commands.OFF: CodeDefinition(
        code="Standby", type=CodeTypes.IRCODE, repeat=2, wait=False
    ),
    ucapi.media_player.Commands.ON: CodeDefinition(
        code="Standby", type=CodeTypes.IRCODE, wait=False
    ),
    ucapi.media_player.Commands.PLAY_PAUSE: CodeDefinition(
        code="Pause", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.PREVIOUS: CodeDefinition(
        code="Enter", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.REWIND: CodeDefinition(
        code="Reverse", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.STOP: CodeDefinition(
        code="Stop", type=CodeTypes.IRCODE
    ),
}
