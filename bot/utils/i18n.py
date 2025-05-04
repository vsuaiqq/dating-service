import gettext
from collections import defaultdict
from pathlib import Path

LOCALES_PATH = Path(__file__).parent.parent / 'locales'
DEFAULT_LANG = 'en'

def _create_translation(lang):
    return gettext.translation(
        domain='messages',
        localedir=LOCALES_PATH,
        languages=[lang],
        fallback=True
    )

_translators = defaultdict(lambda: _create_translation(DEFAULT_LANG))

def get_translator(user):
    locale = getattr(user, 'language_code', DEFAULT_LANG)
    if locale not in _translators:
        _translators[locale] = _create_translation(locale)
    return _translators[locale].gettext
