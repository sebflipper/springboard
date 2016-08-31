import os, logging, colorsys, struct
from cached_property import cached_property
from tingbot import Image
from tingbot.tingapp import TingApp as BaseTingApp

def _hex_color_to_tuple(hex_color):
    try:
        return struct.unpack('BBB', hex_color.decode('hex'))
    except:
        raise ValueError('Could not decode %r as a hex color (should be format "aabbcc")' % hex_color)

def _tuple_to_hex_color(color_tuple):
    color_tuple = (int(c) for c in color_tuple)

    try:
        return struct.pack('BBB', *color_tuple).encode('hex')
    except:
        raise ValueError('Could not encode %r as a hex color (should be a 3-tuple)' % color_tuple)

def _color_multiply(color, multiple):
    return tuple(c * multiple for c in color)

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

    default_background_color = (20, 20, 20)
    
    @cached_property
    def background_color(self):
        try:
            hex_color = self.info['background_color']
        except KeyError:
            return TingApp.default_background_color

        try:
            color = _hex_color_to_tuple(hex_color)
        except:
            logging.exception('Failed to parse hex color, using default')
            return TingApp.default_background_color

        # colorsys works with colors between 0 and 1
        fractional_color = _color_multiply(color, 1/255.0)
        y, i, q = colorsys.rgb_to_yiq(*fractional_color)

        if y > 0.6:
            y = 0.6
            fractional_color = colorsys.yiq_to_rgb(y, i, q)
            color = _color_multiply(fractional_color, 255)
            logging.warning(
                'Background color was too bright (white text must be visible on top of this '
                'color), color "%s" was darkened to "%s"' % (hex_color, _tuple_to_hex_color(color)))

        return color

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
