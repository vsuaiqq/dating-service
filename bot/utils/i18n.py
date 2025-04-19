import gettext
from collections import defaultdict

from pathlib import Path

LOCALES_PATH = Path(__file__).parent.parent / 'locales'
DEFAULT_LANG = 'en'

_translators = defaultdict(lambda: gettext.translation(
    domain='messages',
    localedir=LOCALES_PATH,
    languages=[DEFAULT_LANG],
    fallback=True
))

def get_translator(locale: str):
    return _translators[locale]
