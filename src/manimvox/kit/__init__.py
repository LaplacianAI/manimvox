"""Everything an episode file needs: `from manimvox.kit import *`."""
from manim import *

from . import colours as _colours
from .colours import (  # noqa: F401
                      ACCENT,
                      BG,
                      BLUE,
                      CODE_BG,
                      ERROR,
                      INK,
                      LINE,
                      MUTED,
                      OK,
                      ORANGE,
                      PANEL,
                      PANEL2,
                      PINK,
                      TEAL,
                      VIOLET,
                      WARN,
)
from .components import (  # noqa: F401
                      arrow,
                      box,
                      bullets,
                      card,
                      chip,
                      code,
                      flow,
                      gedge,
                      gnode,
                      heading,
                      lifeline,
                      message,
                      node,
                      note,
                      stat,
                      table,
)
from .episode import Episode, Episode3D  # noqa: F401
from .icons import (  # noqa: F401
                      icon_bot,
                      icon_box,
                      icon_cloud,
                      icon_coin,
                      icon_db,
                      icon_doc,
                      icon_person,
                      icon_phone,
                      icon_shop,
                      icon_till,
)
from .text import AR, ARABIC, FONT, MONO, SAFE_H, SAFE_W, STAGE_BOTTOM, STAGE_CENTER, STAGE_TOP, P, T, fit  # noqa: F401

globals().update(_colours.NAMED)
