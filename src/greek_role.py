import sys

from docutils.parsers.rst import roles
from docutils import nodes

role = roles.GenericRole('gk', nodes.emphasis)

roles.register_local_role('gk', role)
