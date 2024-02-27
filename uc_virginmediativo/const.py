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
    state: ucapi.media_player.States | None = None
    wait: bool = True


# IRCODES not mapped
# "Clear": "Clear"
# "Exit": "Exit"
# "Play": "Play",
# "TV": "LiveTV",
# "Standby": "Standby",

# TELEPORTS not mapped
# "Guide": "GUIDE",
# "Live TV": "LIVETV",

AVAILABLE_COMMANDS: dict[str, CodeDefinition] = {
    "guide": CodeDefinition(code="Guide", display_name="Guide", type=CodeTypes.IRCODE),
    "info": CodeDefinition(code="info", display_name="Info", type=CodeTypes.IRCODE),
    "num0": CodeDefinition(code="num0", display_name="0", type=CodeTypes.IRCODE),
    "num1": CodeDefinition(code="num1", display_name="1", type=CodeTypes.IRCODE),
    "num2": CodeDefinition(code="num2", display_name="2", type=CodeTypes.IRCODE),
    "num3": CodeDefinition(code="num3", display_name="3", type=CodeTypes.IRCODE),
    "num4": CodeDefinition(code="num4", display_name="4", type=CodeTypes.IRCODE),
    "num5": CodeDefinition(code="num5", display_name="5", type=CodeTypes.IRCODE),
    "num6": CodeDefinition(code="num6", display_name="6", type=CodeTypes.IRCODE),
    "num7": CodeDefinition(code="num7", display_name="7", type=CodeTypes.IRCODE),
    "num8": CodeDefinition(code="num8", display_name="8", type=CodeTypes.IRCODE),
    "num9": CodeDefinition(code="num9", display_name="9", type=CodeTypes.IRCODE),
    "record": CodeDefinition(
        code="record", display_name="Record", type=CodeTypes.IRCODE
    ),
    "thumpsdown": CodeDefinition(
        code="thumbsdown", display_name="Thumbs Down", type=CodeTypes.IRCODE
    ),
    "thumpsup": CodeDefinition(
        code="thumbsup", display_name="Thumbs Up", type=CodeTypes.IRCODE
    ),
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
        code="Standby",
        state=ucapi.media_player.States.OFF,
        type=CodeTypes.IRCODE,
        repeat=2,
        wait=False,
    ),
    ucapi.media_player.Commands.ON: CodeDefinition(
        code="Standby",
        state=ucapi.media_player.States.ON,
        type=CodeTypes.IRCODE,
        wait=False,
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
        code="Stop", state=ucapi.media_player.States.PLAYING, type=CodeTypes.IRCODE
    ),
}
