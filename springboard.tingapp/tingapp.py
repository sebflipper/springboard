import os, logging
from cached_property import cached_property
from tingbot import Image
from tingbot.tingapp import TingApp as BaseTingApp

class TingApp(BaseTingApp):
    @cached_property
    def name_image(self):
        return Image.from_text(
            self.name,
            font_size=16,
            color='white',
            antialias=True,
            font='OpenSans-Semibold.ttf',
        )

    def draw(self, surface, centered_at):
        if self.icon:
            surface.image(
                self.icon,
                xy=centered_at,
                align='center',
                scale=1,
            )
        surface.image(
            self.name_image,
            xy=(centered_at[0], centered_at[1]+58),
            align='top',
        )
