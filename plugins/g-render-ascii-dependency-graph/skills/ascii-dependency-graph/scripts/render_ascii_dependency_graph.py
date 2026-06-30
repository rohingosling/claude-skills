#!/usr/bin/env python3
#-----------------------------------------------------------------------------------------------------------------------
# Program: ASCII Dependency Graph Renderer
# Version: 1.0
# Author:  Rohin Gosling
#
# Description:
#
#   Renders ASCII dependency graphs from a JSON description. The JSON describes a tree of nodes; each node has a "name"
#   and two optional links: "right" (a single node placed to the right, forming a horizontal chain via ├──> arrows) and
#   "bottom" (a list of child nodes placed below, branching from the node's centre). An ellipsis marker for arrays is
#   written as {"ellipsis": true} and renders as three vertically stacked · characters.
#
# Usage:
#
#   python render_ascii_dependency_graph.py '<json_string>'
#   python render_ascii_dependency_graph.py --file graph.json
#-----------------------------------------------------------------------------------------------------------------------

import io
import json
import math
import sys


#-----------------------------------------------------------------------------------------------------------------------
# Function: round_up_to_odd
#
# Description:
#
#   Round n up to the nearest odd integer. The value is first ceilinged to an integer, then incremented by one when the
#   result is even.
#
# Arguments:
#
#   n : The number to round up to the nearest odd integer.
#
# Returns:
#
#   The nearest odd integer greater than or equal to n.
#
#-----------------------------------------------------------------------------------------------------------------------

def round_up_to_odd ( n ):

    # Round n up to the nearest odd integer.

    n = math.ceil ( n )

    if n % 2 == 0:
        n += 1

    # Return the rounded-up odd integer to the caller.

    return n


#-----------------------------------------------------------------------------------------------------------------------
# Function: box_width
#
# Description:
#
#   Compute the box width for a node, defined as RoundUpToNearestOddNumber( len(name) + 4 ).
#
# Arguments:
#
#   name : The node name to size a box for.
#
# Returns:
#
#   The box width in characters.
#
#-----------------------------------------------------------------------------------------------------------------------

def box_width ( name ):

    # Compute the box width as the next odd number at or above the name length plus four.

    return round_up_to_odd ( len ( name ) + 4 )


#-----------------------------------------------------------------------------------------------------------------------
# Class: Canvas
#
# Description:
#
#   An expandable 2D character grid. Cells are addressed by row and column; the grid grows on demand so that any cell
#   can be written without pre-sizing.
#
# Attributes:
#
#   lines : The 2D grid, stored as a list of rows where each row is a list of single-character strings.
#-----------------------------------------------------------------------------------------------------------------------

class Canvas:

    #-------------------------------------------------------------------------------------------------------------------
    # Function: __init__
    #
    # Description:
    #
    #   Initialise an empty canvas with no rows.
    #
    # Arguments:
    #
    #   None.
    #
    # Returns:
    #
    #   None.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def __init__ ( self ):

        # Initialise an empty canvas with no rows.

        self.lines = []

    #-------------------------------------------------------------------------------------------------------------------
    # Function: _grow
    #
    # Description:
    #
    #   Grow the grid so that the cell at the given row and column exists. Missing rows are appended as empty lists and
    #   missing columns in the target row are padded with spaces.
    #
    # Arguments:
    #
    #   row : The row index that must exist.
    #   col : The column index that must exist within that row.
    #
    # Returns:
    #
    #   None.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def _grow ( self, row, col ):

        # Grow the grid so that the cell at the given row and column exists.

        # Append empty rows until the target row exists.

        while len ( self.lines ) <= row:
            self.lines.append ( [] )

        # Pad the target row with spaces until the target column exists.

        while len ( self.lines [ row ] ) <= col:
            self.lines [ row ].append ( ' ' )

    #-------------------------------------------------------------------------------------------------------------------
    # Function: put
    #
    # Description:
    #
    #   Write a single character to the cell at the given row and column, growing the grid first as needed.
    #
    # Arguments:
    #
    #   row : The target row index.
    #   col : The target column index.
    #   ch  : The single character to write.
    #
    # Returns:
    #
    #   None.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def put ( self, row, col, ch ):

        # Write a single character to the cell at the given row and column.

        self._grow ( row, col )
        self.lines [ row ] [ col ] = ch

    #-------------------------------------------------------------------------------------------------------------------
    # Function: puts
    #
    # Description:
    #
    #   Write a string to the grid starting at the given row and column, placing each character in successive columns.
    #
    # Arguments:
    #
    #   row  : The target row index.
    #   col  : The starting column index.
    #   text : The string to write across successive columns.
    #
    # Returns:
    #
    #   None.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def puts ( self, row, col, text ):

        # Write a string to the grid starting at the given row and column.

        for i, ch in enumerate ( text ):
            self.put ( row, col + i, ch )

    #-------------------------------------------------------------------------------------------------------------------
    # Function: render
    #
    # Description:
    #
    #   Render the grid to a string. Each row is joined into a line with trailing whitespace stripped, the rows are
    #   joined with newlines, and trailing blank lines are removed.
    #
    # Arguments:
    #
    #   None.
    #
    # Returns:
    #
    #   The rendered ASCII grid as a single string.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def render ( self ):

        # Render the grid to a string, stripping trailing whitespace and trailing blank lines.

        return '\n'.join (
            ''.join ( line ).rstrip () for line in self.lines
        ).rstrip ( '\n' )


#-----------------------------------------------------------------------------------------------------------------------
# Function: flatten_chain
#
# Description:
#
#   Follow the "right" links from a node and return the list of nodes forming the horizontal chain, in left-to-right
#   order.
#
# Arguments:
#
#   node : The leftmost node of the chain to flatten.
#
# Returns:
#
#   The list of nodes in the chain.
#
#-----------------------------------------------------------------------------------------------------------------------

def flatten_chain ( node ):

    # Follow the "right" links from a node and return the list of nodes forming the chain.

    chain = []
    cur   = node

    # Walk the "right" links, appending each node until the chain ends.

    while cur is not None:
        chain.append ( cur )
        cur = cur.get ( 'right' )

    # Return the flattened chain to the caller.

    return chain


#-----------------------------------------------------------------------------------------------------------------------
# Function: compute_positions
#
# Description:
#
#   Compute the layout of a horizontal chain. For each node it returns a dict with the node's left column, box width,
#   and centre column. Boxes are separated by a three-character gap (──>).
#
# Arguments:
#
#   chain     : The list of nodes in the chain, in left-to-right order.
#   start_col : The left column at which the first box begins.
#
# Returns:
#
#   A list of { col, width, center } dicts, one per node in the chain.
#
#-----------------------------------------------------------------------------------------------------------------------

def compute_positions ( chain, start_col ):

    # Compute the column, width, and centre of each node's box in the chain.

    positions = []
    col       = start_col

    # Size each node's box and advance the running column past it and the three-character gap.

    for node in chain:
        w = box_width ( node [ 'name' ] )
        positions.append ( { 'col': col, 'width': w, 'center': col + w // 2 } )
        col += w + 3                       # gap = ──> (3 chars)

    # Return the per-node layout positions to the caller.

    return positions


#-----------------------------------------------------------------------------------------------------------------------
# Function: draw_verticals
#
# Description:
#
#   Draw a │ character at every column in the given set, on the given row. Used to extend ancestor vertical lines down
#   through each rendered row.
#
# Arguments:
#
#   canvas  : The canvas to draw on.
#   row     : The row to draw the vertical bars on.
#   columns : The set of column positions to draw a │ at.
#
# Returns:
#
#   None.
#
#-----------------------------------------------------------------------------------------------------------------------

def draw_verticals ( canvas, row, columns ):

    # Draw a │ at every column in the set, on the given row.

    for c in columns:
        canvas.put ( row, c, '│' )


#-----------------------------------------------------------------------------------------------------------------------
# Function: draw_chain_top
#
# Description:
#
#   Draw the top-border row for a horizontal chain, rendering each node's box as ┌──...──┐.
#
# Arguments:
#
#   canvas    : The canvas to draw on.
#   row       : The row to draw the top borders on.
#   chain     : The list of nodes in the chain.
#   positions : The layout positions returned by compute_positions for the chain.
#
# Returns:
#
#   None.
#
#-----------------------------------------------------------------------------------------------------------------------

def draw_chain_top ( canvas, row, chain, positions ):

    # Draw the top-border row for a horizontal chain.

    for i, node in enumerate ( chain ):

        # Look up this node's box position and width.

        p = positions [ i ]
        w = p [ 'width' ]

        # Draw the top-left corner of the box.

        canvas.put ( row, p [ 'col' ], '┌' )

        # Draw the horizontal top edge between the corners.

        for j in range ( 1, w - 1 ):
            canvas.put ( row, p [ 'col' ] + j, '─' )

        # Draw the top-right corner of the box.

        canvas.put ( row, p [ 'col' ] + w - 1, '┐' )


#-----------------------------------------------------------------------------------------------------------------------
# Function: draw_chain_text
#
# Description:
#
#   Draw the text row for a horizontal chain. Each node renders its name between vertical borders; nodes with a node to
#   their right close with ├ and emit a ──> arrow into the gap, while the last node closes with │.
#
# Arguments:
#
#   canvas    : The canvas to draw on.
#   row       : The row to draw the text and arrows on.
#   chain     : The list of nodes in the chain.
#   positions : The layout positions returned by compute_positions for the chain.
#
# Returns:
#
#   None.
#
#-----------------------------------------------------------------------------------------------------------------------

def draw_chain_text ( canvas, row, chain, positions ):

    # Draw the text row for a horizontal chain, including the ├──> arrows between boxes.

    for i, node in enumerate ( chain ):

        # Look up this node's position, width, name, and whether it has a node to its right.

        p         = positions [ i ]
        w         = p [ 'width' ]
        name      = node [ 'name' ]
        has_right = i < len ( chain ) - 1

        # Draw the left border, a leading space, and the node name.

        canvas.put ( row, p [ 'col' ], '│' )
        canvas.put ( row, p [ 'col' ] + 1, ' ' )
        canvas.puts ( row, p [ 'col' ] + 2, name )

        # Pad the remaining interior of the box with spaces.

        for j in range ( p [ 'col' ] + 2 + len ( name ), p [ 'col' ] + w - 1 ):
            canvas.put ( row, j, ' ' )

        # Draw the right border as ├ when a node follows, otherwise │.

        canvas.put ( row, p [ 'col' ] + w - 1, '├' if has_right else '│' )

        # Emit a ──> arrow into the gap when a node follows.

        if has_right:
            a = p [ 'col' ] + w
            canvas.puts ( row, a, '──>' )


#-----------------------------------------------------------------------------------------------------------------------
# Function: draw_chain_bottom
#
# Description:
#
#   Draw the bottom-border row for a horizontal chain, rendering each node's box as └──...──┘. A node that has bottom
#   dependencies places a ┬ at its centre column instead of ─ so a vertical branch can descend from it.
#
# Arguments:
#
#   canvas    : The canvas to draw on.
#   row       : The row to draw the bottom borders on.
#   chain     : The list of nodes in the chain.
#   positions : The layout positions returned by compute_positions for the chain.
#
# Returns:
#
#   None.
#
#-----------------------------------------------------------------------------------------------------------------------

def draw_chain_bottom ( canvas, row, chain, positions ):

    # Draw the bottom-border row for a horizontal chain, placing a ┬ at the centre of any node with bottom deps.

    for i, node in enumerate ( chain ):

        # Look up this node's position, width, centre column, and whether it has bottom deps.

        p          = positions [ i ]
        w          = p [ 'width' ]
        center     = p [ 'center' ]
        has_bottom = bool ( node.get ( 'bottom' ) )

        # Draw the bottom-left corner of the box.

        canvas.put ( row, p [ 'col' ], '└' )

        # Draw the horizontal bottom edge, placing a ┬ at the centre when the node has bottom deps.

        for j in range ( 1, w - 1 ):
            gc = p [ 'col' ] + j
            canvas.put ( row, gc, '┬' if ( has_bottom and gc == center ) else '─' )

        # Draw the bottom-right corner of the box.

        canvas.put ( row, p [ 'col' ] + w - 1, '┘' )


#-----------------------------------------------------------------------------------------------------------------------
# Function: render_subtree
#
# Description:
#
#   Render a node's horizontal chain and all of its bottom dependencies. The chain occupies three rows (top border,
#   text, bottom border); below it each chain member that has bottom deps spawns a vertical dependency list. The
#   bottom-dep sections are processed right-to-left so the rightmost centre's deps appear directly under the chain and
#   leftward centres continue later, with each leftward centre's column carried as an active vertical for the sections
#   below it.
#
# Arguments:
#
#   canvas           : The canvas to draw on.
#   row              : The top row at which to render the chain.
#   col              : The left column at which the chain's first box begins.
#   node             : The leftmost node of the chain to render.
#   active_verticals : The set of column positions where ancestor │ lines must be drawn on every row.
#
# Returns:
#
#   The next available row below everything rendered.
#
#-----------------------------------------------------------------------------------------------------------------------

def render_subtree ( canvas, row, col, node, active_verticals ):

    # Render a node's horizontal chain and all of its bottom dependencies.

    chain     = flatten_chain ( node )
    positions = compute_positions ( chain, col )

    # Draw the three chain rows: top borders, text, and bottom borders, each preceded by the ancestor verticals.

    draw_verticals ( canvas, row, active_verticals )
    draw_chain_top ( canvas, row, chain, positions )

    draw_verticals ( canvas, row + 1, active_verticals )
    draw_chain_text ( canvas, row + 1, chain, positions )

    draw_verticals ( canvas, row + 2, active_verticals )
    draw_chain_bottom ( canvas, row + 2, chain, positions )

    # Collect the centre column and bottom deps of every chain member that has bottom deps.

    bottoms = []

    for i, n in enumerate ( chain ):
        if n.get ( 'bottom' ):
            bottoms.append ( ( positions [ i ] [ 'center' ], n [ 'bottom' ] ) )

    # Process right-to-left so the rightmost centre's deps appear directly under the chain and leftward centres continue
    # later.

    bottoms.reverse ()

    next_row = row + 3

    for b_idx, ( center, deps ) in enumerate ( bottoms ):

        left_centres   = { c for c, _ in bottoms [ b_idx + 1 : ] }
        section_active = active_verticals | left_centres
        next_row       = render_deps_list ( canvas, next_row, center, deps, section_active )

    # Return the next available row to the caller.

    return next_row


#-----------------------------------------------------------------------------------------------------------------------
# Function: render_deps_list
#
# Description:
#
#   Render a vertical list of dependencies branching from a centre column. Each dependency is drawn as its own
#   horizontal chain, connected to the centre by a ├──> arrow (or └──> for the last sibling). An ellipsis dependency
#   ({"ellipsis": true}) renders as three vertically stacked · characters. The function manages the centre's own
#   │/├/└ glyphs; the active_verticals set passed in carries only the ancestor │ columns and does NOT include
#   center_col. Each dependency may recurse into its own bottom deps, and a blank separator row is emitted after a
#   non-last dependency whose own box carried a ┬.
#
# Arguments:
#
#   canvas           : The canvas to draw on.
#   row              : The top row at which to begin rendering the list.
#   center_col       : The centre column from which the dependencies branch.
#   deps             : The list of dependency nodes (or ellipsis markers) to render.
#   active_verticals : The ancestor │ columns; does not include center_col, which this function manages itself.
#
# Returns:
#
#   The next available row below the rendered list.
#
#-----------------------------------------------------------------------------------------------------------------------

def render_deps_list ( canvas, row, center_col, deps, active_verticals ):

    # Render a vertical list of dependencies branching from the centre column.

    for i, dep in enumerate ( deps ):

        is_last = ( i == len ( deps ) - 1 )

        # Ellipsis marker: render three vertically stacked · characters and continue.

        if isinstance ( dep, dict ) and dep.get ( 'ellipsis' ):

            # Draw three stacked · characters at the centre column, extending the ancestor verticals on each row.

            for _ in range ( 3 ):
                draw_verticals ( canvas, row, active_verticals )
                canvas.put ( row, center_col, '·' )
                row += 1

            # Skip to the next dependency.

            continue

        # Normal dependency: lay out its own chain, offset four columns past the ├──> arrow.

        dep_chain     = flatten_chain ( dep )
        box_col       = center_col + 4               # after ├──>
        dep_positions = compute_positions ( dep_chain, box_col )
        all_v         = active_verticals | { center_col }

        # Row 0: draw the top borders, extending the centre's │ down alongside the ancestor verticals.

        draw_verticals ( canvas, row, all_v )
        draw_chain_top ( canvas, row, dep_chain, dep_positions )

        # Row 1: draw the arrow connector (└──> for the last sibling, ├──> otherwise) and the dependency text.

        draw_verticals ( canvas, row + 1, active_verticals )
        arrow = '└' if is_last else '├'
        canvas.puts ( row + 1, center_col, arrow + '──>' )
        draw_chain_text ( canvas, row + 1, dep_chain, dep_positions )

        # Row 2: draw the bottom borders, continuing the centre's │ only when this is not the last sibling.

        if is_last:
            draw_verticals ( canvas, row + 2, active_verticals )
        else:
            draw_verticals ( canvas, row + 2, all_v )
        draw_chain_bottom ( canvas, row + 2, dep_chain, dep_positions )

        # Recurse into the dependency chain's own bottom deps, processed right-to-left and carrying the centre's │
        # as an active vertical for every sibling but the last.

        dep_bottoms = []

        for j, n in enumerate ( dep_chain ):
            if n.get ( 'bottom' ):
                dep_bottoms.append ( ( dep_positions [ j ] [ 'center' ], n [ 'bottom' ] ) )

        dep_bottoms.reverse ()

        # Render each bottom-dep section below the dependency chain, advancing the running row.

        next_row = row + 3

        for b_idx, ( dep_center, dep_deps ) in enumerate ( dep_bottoms ):

            left_centres = { c for c, _ in dep_bottoms [ b_idx + 1 : ] }

            # Carry the centre's │ as an active vertical for every sibling but the last, plus the leftward centres.

            if is_last:
                section_active = active_verticals | left_centres
            else:
                section_active = active_verticals | { center_col } | left_centres

            # Render this bottom-dep section and advance to the next available row.

            next_row = render_deps_list ( canvas, next_row, dep_center, dep_deps, section_active )

        # Advance past everything rendered for this dependency.

        row = next_row

        # Emit a blank separator row after a dependency whose own box carried a ┬ and which is not the last sibling.

        if dep.get ( 'bottom' ) and not is_last:
            draw_verticals ( canvas, row, active_verticals | { center_col } )
            row += 1

    # Return the next available row to the caller.

    return row


#-----------------------------------------------------------------------------------------------------------------------
# Function: render_graph
#
# Description:
#
#   Render a dependency graph dict and return the resulting ASCII string. Creates a canvas, renders the root subtree at
#   the origin with no active verticals, and returns the rendered grid.
#
# Arguments:
#
#   graph_data : The dependency graph as a nested dict of nodes.
#
# Returns:
#
#   The rendered dependency graph as an ASCII string.
#
#-----------------------------------------------------------------------------------------------------------------------

def render_graph ( graph_data ):

    # Render a dependency graph dict and return the ASCII string.

    canvas = Canvas ()
    render_subtree ( canvas, 0, 0, graph_data, set () )
    return canvas.render ()


#-----------------------------------------------------------------------------------------------------------------------
# Function: main
#
# Description:
#
#   Command-line entry point. Reads the graph JSON either from the first argument or, when the first argument is --file,
#   from the file named by the second argument, renders the graph, and prints it. Exits with status 1 on a missing
#   argument or a missing --file path.
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

    # Parse the command-line arguments, load the graph JSON, render it, and print the result.

    # Print usage and exit with status 1 when no argument is given.

    if len ( sys.argv ) < 2:
        print ( "Usage: render_ascii_dependency_graph.py '<json>' | --file <path>",
                file = sys.stderr )
        sys.exit ( 1 )

    # Branch on whether the first argument selects file input.

    if sys.argv [ 1 ] == '--file':

        # Require a path after --file, then load the graph JSON from that file.

        if len ( sys.argv ) < 3:
            print ( "Error: --file requires a path argument", file = sys.stderr )
            sys.exit ( 1 )
        with open ( sys.argv [ 2 ], 'r', encoding = 'utf-8' ) as f:
            data = json.load ( f )
    else:

        # Parse the graph JSON directly from the first argument.

        data = json.loads ( sys.argv [ 1 ] )

    # Render the graph and print the resulting ASCII string.

    print ( render_graph ( data ) )


#-----------------------------------------------------------------------------------------------------------------------
# Program entry point.
#-----------------------------------------------------------------------------------------------------------------------


#-----------------------------------------------------------------------------------------------------------------------
# Program Entry Point
#-----------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

    sys.stdout = io.TextIOWrapper ( sys.stdout.buffer, encoding = 'utf-8' )
    main ()
