#!/usr/bin/env python3
#-----------------------------------------------------------------------------------------------------------------------
# Program: ASCII Hierarchy Diagram Renderer
# Version: 1.1
# Author:  Rohin Gosling
#
# Description:
#
#   Renders a hierarchical ASCII tree diagram from a JSON structure. Each node carries a "name" and an optional
#   "comment"; children are nested under a "children" list. Tree connectors are drawn with box-drawing characters
#   (non-last child "├─ ", last child "└─ ", non-last parent continuation "│  ", last parent "   ") and any node
#   comments are aligned into a trailing comment column. A blank separator line is emitted after every completed
#   sub-tree at every depth, so each branch is visually separated from the sibling that follows it.
#
# Usage:
#
#   python render_ascii_hierarchy_diagram.py --file tree.json --include-root
#   python render_ascii_hierarchy_diagram.py --file tree.json --no-include-root
#-----------------------------------------------------------------------------------------------------------------------

import json
import argparse
import sys
import io


#-----------------------------------------------------------------------------------------------------------------------
# Function: build_tree_lines
#
# Description:
#
#   Recursively build a list of (line_text, comment) pairs for a subtree. Each node produces one line with the
#   appropriate tree connectors, and children are rendered with continuation prefixes derived from their parent's
#   position. The root node is rendered as its bare name; every other node is prefixed with a connector ("└─ " for
#   the last child, "├─ " otherwise). Children inherit a continuation prefix of "   " when their parent is the last
#   child and "│  " otherwise (3 characters per depth level).
#
#   After a child's own subtree is emitted, a blank separator line (carrying the vertical continuation glyph at that
#   child's column) is appended when the child has its OWN children AND is not the last sibling. This places a visual
#   gap after every completed sub-tree at EVERY depth, while leaf children and the final sibling are left ungapped.
#
# Arguments:
#
#   node    : The current node dict, with a "name", an optional "comment", and optional "children" list.
#   prefix  : The accumulated continuation prefix string for this node's depth.
#   is_last : Whether this node is the last child of its parent.
#   is_root : Whether this node is the tree root (rendered as a bare name with no connector).
#
# Returns:
#
#   A list of (line_text, comment) pairs for this subtree.
#
#-----------------------------------------------------------------------------------------------------------------------

def build_tree_lines ( node, prefix, is_last, is_root ):

    # Recursively build the (line_text, comment) pairs for this subtree.

    lines   = []
    name    = node [ "name" ]
    comment = node.get ( "comment", "" )

    # Render this node: a bare name for the root, otherwise a connector-prefixed line.

    if is_root:
        line_text = name
    else:
        connector = "└─ " if is_last else "├─ "
        line_text = prefix + connector + name

    lines.append ( ( line_text, comment ) )

    # Recurse into the children, extending each child's prefix with the correct continuation.

    children = node.get ( "children", [] )

    for i, child in enumerate ( children ):

        # Flag whether this child is the last in the list.

        child_is_last = ( i == len ( children ) - 1 )

        # Build the child's continuation prefix: empty under the root, otherwise this node's prefix extended.

        if is_root:
            child_prefix = ""
        else:
            continuation = "   " if is_last else "│  "
            child_prefix = prefix + continuation

        # Recurse into the child and append its lines.

        lines.extend ( build_tree_lines ( child, child_prefix, child_is_last, is_root = False ) )

        # Gap after a completed sub-tree: a non-last child that has its own children is followed by a separator
        # line continuing the vertical rule at the child's column. Leaf children and the last sibling get no gap.

        if child.get ( "children" ) and not child_is_last:
            lines.append ( ( child_prefix + "│", "" ) )

    # Return the collected lines to caller.

    return lines


#-----------------------------------------------------------------------------------------------------------------------
# Function: format_lines_with_comments
#
# Description:
#
#   Format tree lines with aligned trailing comments using a two-pass approach. Pass 1 finds the longest line_text
#   across all lines. Pass 2 sets the comment margin to longest_line_length + 4, pads each line to that margin width
#   and appends its comment when present; lines without a comment are emitted without trailing padding.
#
# Arguments:
#
#   lines : A list of (line_text, comment) pairs to format.
#
# Returns:
#
#   A list of formatted line strings with aligned trailing comments.
#
#-----------------------------------------------------------------------------------------------------------------------

def format_lines_with_comments ( lines ):

    # Format tree lines with aligned trailing comments.

    # Pass 1: find the longest line_text and derive the comment margin (longest line length + 4).

    max_length = max ( ( len ( line_text ) for line_text, _ in lines ), default = 0 )
    margin     = max_length + 4

    # Pass 2: pad each line to the margin and append its comment; emit comment-less lines without padding.

    result = []

    for line_text, comment in lines:

        if comment:
            result.append ( line_text.ljust ( margin ) + comment )
        else:
            result.append ( line_text )

    # Return the formatted lines to caller.

    return result


#-----------------------------------------------------------------------------------------------------------------------
# Function: render_include_root
#
# Description:
#
#   Render the full tree including the root node. One global comment margin is computed across the entire tree, so
#   all comments align to a single column. A blank separator line is inserted after every completed sub-tree at every
#   depth (see build_tree_lines): a top-level child that has its own children and is not the last sibling is followed
#   by a "│" separator, and deeper sub-trees are gapped by build_tree_lines itself.
#
# Arguments:
#
#   root : The root node dict to render.
#
# Returns:
#
#   The rendered tree as a single newline-joined string.
#
#-----------------------------------------------------------------------------------------------------------------------

def render_include_root ( root ):

    # Render the full tree including the root node, with one global comment margin.

    all_lines = []
    all_lines.append ( ( root [ "name" ], root.get ( "comment", "" ) ) )

    # Append each top-level child group, inserting a "│" separator line after each completed sub-tree.

    children = root.get ( "children", [] )

    for i, child in enumerate ( children ):

        # Build this child group's lines, flagging whether it is the last top-level group.

        child_is_last = ( i == len ( children ) - 1 )
        child_lines   = build_tree_lines ( child, prefix = "", is_last = child_is_last, is_root = False )

        # Append this group's lines to the combined output.

        all_lines.extend ( child_lines )

        # Insert a "│" separator after this top-level sub-tree, matching the all-depth rule in build_tree_lines:
        # only a non-last child that has its own children is followed by a separator.

        if not child_is_last and child.get ( "children" ):
            all_lines.append ( ( "│", "" ) )

    # Format the combined lines with a single shared comment margin and return them to caller.

    formatted = format_lines_with_comments ( all_lines )
    return "\n".join ( formatted )


#-----------------------------------------------------------------------------------------------------------------------
# Function: render_no_include_root
#
# Description:
#
#   Render each top-level child as an independent tree, omitting the root node. Each group computes its own comment
#   margin (rather than sharing one global margin), and groups are separated by a blank line. Within each group,
#   sub-trees are gapped at every depth by build_tree_lines.
#
# Arguments:
#
#   root : The root node dict whose children are rendered as independent trees.
#
# Returns:
#
#   The rendered groups as a single newline-joined string.
#
#-----------------------------------------------------------------------------------------------------------------------

def render_no_include_root ( root ):

    # Render each top-level child as an independent tree, each with its own comment margin.

    children = root.get ( "children", [] )
    groups   = []

    # Render each top-level child as an independent tree with its own comment margin.

    for child in children:

        lines     = build_tree_lines ( child, prefix = "", is_last = True, is_root = True )
        formatted = format_lines_with_comments ( lines )

        # Collect this group's formatted lines.

        groups.append ( formatted )

    # Concatenate the formatted groups, separating each group from the next with a blank line.

    output_lines = []

    for i, group in enumerate ( groups ):

        # Append this group's lines to the output.

        output_lines.extend ( group )

        # Insert a blank separator line after this group unless it is the last one.

        if i < len ( groups ) - 1:
            output_lines.append ( "" )

    # Return the joined output to caller.

    return "\n".join ( output_lines )


#-----------------------------------------------------------------------------------------------------------------------
# Function: main
#
# Description:
#
#   Command-line entry point. Reconfigures stdout to UTF-8 so box-drawing characters render correctly, parses the
#   --file argument and the mutually-exclusive --include-root / --no-include-root mode flags, loads the JSON tree,
#   renders it with the selected mode, and prints the result.
#
# Arguments:
#
#   None.
#
# Returns:
#
#   None.
#
#-----------------------------------------------------------------------------------------------------------------------

def main ():

    # Command-line entry point: parse arguments, load the JSON tree, render it, and print the result.

    # Reconfigure stdout to UTF-8 so the box-drawing connectors render correctly.

    sys.stdout = io.TextIOWrapper ( sys.stdout.buffer, encoding = "utf-8" )

    # Build the argument parser: a required --file and a required mutually-exclusive root-inclusion mode.

    parser = argparse.ArgumentParser ( description = "Render a hierarchical ASCII tree diagram." )
    parser.add_argument ( "--file", required = True, help = "Path to JSON input file." )

    # Add a required mutually-exclusive group for the root-inclusion mode.

    mode_group = parser.add_mutually_exclusive_group ( required = True )

    # Add the --include-root flag, which keeps the root node in the output.

    mode_group.add_argument (
        "--include-root",
        action = "store_true",
        dest   = "include_root",
        help   = "Include the root node in the output."
    )

    # Add the --no-include-root flag, which renders each top-level child independently.

    mode_group.add_argument (
        "--no-include-root",
        action = "store_true",
        dest   = "no_include_root",
        help   = "Skip the root node; render each top-level child independently."
    )

    # Parse the command-line arguments.

    arguments = parser.parse_args ()

    # Load the JSON tree from the input file.

    with open ( arguments.file, "r", encoding = "utf-8" ) as file:
        root = json.load ( file )

    # Render the tree with the selected mode, then print it.

    if arguments.include_root:
        output = render_include_root ( root )
    else:
        output = render_no_include_root ( root )

    # Print the rendered tree.

    print ( output )


#-----------------------------------------------------------------------------------------------------------------------
# Program Entry Point
#-----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    main ()
