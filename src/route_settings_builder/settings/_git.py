from envparse import env
from pygit2 import Repository

try:
    CURRENT_BRANCH = Repository('.').head.shorthand
except Exception:  # pylint: disable=catching-too-general-exception
    CURRENT_BRANCH = env.str('CURRENT_BRANCH', default='main')
