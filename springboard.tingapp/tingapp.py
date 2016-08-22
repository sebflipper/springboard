import os, logging
from cached_property import cached_property
from tingbot import Image

class TingApp(object):
    def __init__(self, path):
        self.path = path

    @cached_property
    def info(self):
        info_path = os.path.join(self.path, 'app.tbinfo')
        try:
            with open(info_path) as f:
                return json.load(f)
        except:
            logging.exception('Failed to get app info at %s', info_path)
            return {}

    @property
    def name(self):
        if 'name' in self.info:
            return self.info['name']
        else:
            basename = os.path.basename(self.path)
            name, ext = os.path.splitext(basename)
            return name

    @cached_property
    def name_image(self):
        return Image.from_text(
            self.name,
            font_size=16,
            color='white',
            antialias=True,
            font='OpenSans-Semibold.ttf',
        )

    @cached_property
    def icon(self):
        image_path = os.path.join(self.path, 'icon-48.png')

        if not os.path.isfile(image_path):
            logging.warning(
                'Icon not found for app %s, expected an image at %s',
                self.path,
                image_path)
            return None

        try:
            image = Image.load(image_path)
        except:
            logging.exception('Failed to load image at %s', image_path)
            return None

        return image

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
            xy=(centered_at[0], centered_at[1]+57),
            align='top',
        )
