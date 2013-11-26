# -*- coding: utf-8 -*-
"""antimarkdown.handlers -- Element handlers for converting HTML Elements/subtrees to Markdown text.
"""
from collections import deque

from antimarkdown import nodes


def render(*domtrees):
    if not domtrees:
        return u''

    root = nodes.Root()
    for dom in domtrees:
        build_render_tree(root, dom)
    lines = unicode(root).rstrip().splitlines()

    # Strip leading empty lines
    while not lines[0].strip():
        lines.pop(0)

    return nodes.normalize(u'\n'.join(lines))


def build_render_tree(root, domtree):
    """Process an ElementTree domtree and build a render tree.
    """
    opened = set()
    stack = deque([domtree])
    blackboard = {}
    render_tree = root
    current_node = render_tree

    while stack:
        domtree = stack.pop()

        if domtree not in opened:
            # Open the domtree

            # Build the render node.
            node_class = getattr(nodes, domtree.tag.upper(), nodes.Node)
            current_node = node_class(current_node, domtree, blackboard)

            stack.append(domtree)

            # Queue children
            for el in reversed(domtree):
                stack.append(el)

            opened.add(domtree)
        else:
            # Close the domtree
            current_node = current_node.parent

    return root
