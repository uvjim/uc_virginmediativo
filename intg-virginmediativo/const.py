"""Constants."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Callable

import ucapi


class PollerType(StrEnum):
    """Available pollers."""

    STATUS = "status"


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
    wait_repeat: float | None = None


# IRCODES not mapped
# "Play": "Play",
# "Standby": "Standby",
# "TV": "tv",

# TELEPORTS not mapped
# "Guide": "GUIDE",
# "Live TV": "LIVETV",

AVAILABLE_COMMANDS: dict[str, CodeDefinition] = {
    "CLEAR": CodeDefinition(
        code="clear",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    "PAUSE": CodeDefinition(
        code="pause",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    "PLAY": CodeDefinition(
        code="play",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    "THUMBSDOWN": CodeDefinition(
        code="thumbsdown",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    "THUMBSUP": CodeDefinition(
        code="thumbsup",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.BACK: CodeDefinition(
        code="Exit", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.CHANNEL_DOWN: CodeDefinition(
        code="ChannelDown", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.CHANNEL_UP: CodeDefinition(
        code="ChannelUp", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.CURSOR_DOWN: CodeDefinition(
        code="Down",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.CURSOR_ENTER: CodeDefinition(
        code="Select", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.CURSOR_LEFT: CodeDefinition(
        code="Left",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.CURSOR_RIGHT: CodeDefinition(
        code="Right",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.CURSOR_UP: CodeDefinition(
        code="Up",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.DIGIT_0: CodeDefinition(
        code="num0", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.DIGIT_1: CodeDefinition(
        code="num1", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.DIGIT_2: CodeDefinition(
        code="num2", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.DIGIT_3: CodeDefinition(
        code="num3", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.DIGIT_4: CodeDefinition(
        code="num4", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.DIGIT_5: CodeDefinition(
        code="num5", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.DIGIT_6: CodeDefinition(
        code="num6", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.DIGIT_7: CodeDefinition(
        code="num7", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.DIGIT_8: CodeDefinition(
        code="num8", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.DIGIT_9: CodeDefinition(
        code="num9", type=CodeTypes.IRCODE
    ),
    ucapi.media_player.Commands.FAST_FORWARD: CodeDefinition(
        code="Forward",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.FUNCTION_BLUE: CodeDefinition(
        code="Action_D",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.FUNCTION_GREEN: CodeDefinition(
        code="Action_B",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.FUNCTION_RED: CodeDefinition(
        code="Action_A",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.FUNCTION_YELLOW: CodeDefinition(
        code="Action_C",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.GUIDE: CodeDefinition(
        code="Guide",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.HOME: CodeDefinition(
        code="TIVO",
        type=CodeTypes.TELEPORT,
        wait=False,
    ),
    ucapi.media_player.Commands.INFO: CodeDefinition(
        code="Info",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.LIVE: CodeDefinition(
        code="LIVETV",
        type=CodeTypes.TELEPORT,
        wait=False,
    ),
    ucapi.media_player.Commands.MY_RECORDINGS: CodeDefinition(
        code="NOWPLAYING",
        type=CodeTypes.TELEPORT,
        wait=False,
    ),
    ucapi.media_player.Commands.OFF: CodeDefinition(
        code="Standby",
        state="OFF",
        type=CodeTypes.IRCODE,
        repeat=2,
        wait=False,
        wait_repeat=0.3,
    ),
    ucapi.media_player.Commands.ON: CodeDefinition(
        code="Standby",
        state="ON",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.PLAY_PAUSE: CodeDefinition(
        code="Pause",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.PREVIOUS: CodeDefinition(
        code="Enter",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.RECORD: CodeDefinition(
        code="record",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.REWIND: CodeDefinition(
        code="Reverse",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
    ucapi.media_player.Commands.STOP: CodeDefinition(
        code="Stop",
        type=CodeTypes.IRCODE,
        wait=False,
    ),
}

POLLER_FUNCS: dict[PollerType, Callable] = {}
