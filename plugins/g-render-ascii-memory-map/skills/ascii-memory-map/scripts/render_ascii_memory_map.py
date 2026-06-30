#!/usr/bin/env python3
#-----------------------------------------------------------------------------------------------------------------------
# Program: ASCII Memory Map Renderer
# Version: 1.0
# Author:  Rohin Gosling
#
# Description:
#
#   Renders an ASCII memory map (an address-space layout diagram) from a JSON description. The tool separates the DATA
#   of a memory map (the blocks, their labels, descriptions, outside comments, and numeric addresses) from its RENDERING
#   (address format, box style, height scaling, origin direction, ...). All of the deterministic layout work -- address
#   formatting, column alignment, box drawing, and size-proportional block heights -- is performed here, so a calling
#   agent only has to author compact JSON and relay the rendered result.
#
# Positioning rules:
#
#   The text-placement taxonomy this renderer enforces:
#
#   - Address        : a boundary coordinate  -> left gutter, on the divider that opens the block (low-address edge).
#   - Label          : the block's short name -> inside the box, first body row.
#   - Description     : optional elaboration   -> inside the box, further rows.
#   - Comment / note  : extrinsic annotation   -> right of the box, anchored to the first body row with an arrow;
#                       continuations align beneath it with no arrow.
#   - Divider / border lines carry only the address -- never a label or a comment.
#
#   See SKILL.md for the full schema and the complete parameter reference.
#
# Usage:
#
#   python3 render_ascii_memory_map.py map.json
#   python3 render_ascii_memory_map.py --file map.json --address-format c --origin bottom
#-----------------------------------------------------------------------------------------------------------------------

import argparse
import json
import math
import sys

# Box-drawing glyph sets, keyed by --style. Each maps the eight glyphs used to draw a box: horizontal, vertical, the
# four corners, and the left/right tee junctions for interior dividers.

BOX_STYLES = {
    'unicode': { 'h': '─', 'v': '│', 'tl': '┌', 'tr': '┐', 'ml': '├', 'mr': '┤', 'bl': '└', 'br': '┘' },
    'heavy': { 'h': '━', 'v': '┃', 'tl': '┏', 'tr': '┓', 'ml': '┣', 'mr': '┫', 'bl': '┗', 'br': '┛' },
    'double': { 'h': '═', 'v': '║', 'tl': '╔', 'tr': '╗', 'ml': '╠', 'mr': '╣', 'bl': '╚', 'br': '╝' },
    'ascii': { 'h': '-', 'v': '|', 'tl': '+', 'tr': '+', 'ml': '+', 'mr': '+', 'bl': '+', 'br': '+' },
}

# Default outside-comment arrow per box style. A pure-ASCII style uses '<-' so the map stays legible without Unicode.

DEFAULT_ARROW = { 'unicode': '◄─', 'heavy': '◄─', 'double': '◄─', 'ascii': '<-' }

# Built-in rendering defaults. The JSON "render" block overrides these, and explicit CLI flags override that.

DEFAULTS = {
    'address_format': 'commodore',
    'address_width': None,
    'input_radix': 'hex',
    'hex_case': 'upper',
    'origin': 'top',
    'scale': True,
    'scale_mode': 'log',
    'min_rows': 1,
    'max_rows': 6,
    'style': 'unicode',
    'width': 'auto',
    'comment_arrow': None,
    'show_comments': True,
    'show_size': False,
    'show_end': False,
    'show_gaps': False,
    'gap_label': '· · ·',
    'paragraph': 16,
    'title': None,
}


#-----------------------------------------------------------------------------------------------------------------------
# Function: parse_address
#
# Description:
#
#   Parse a JSON address (int or string) into an integer. Integers are taken verbatim as decimal. Strings accept
#   '$XXXX' / '0xXXXX' / 'XXXXh' (hex), 'SSSS:OOOO' (segmented seg:offset), or a bare numeral parsed in input_radix
#   (default 16).
#
# Arguments:
#
#   value       : The address as a JSON integer or string.
#   input_radix : Radix used to read a bare numeral string (default 16).
#   paragraph   : Bytes per segment, used to fold a segmented 'SSSS:OOOO' address.
#
# Returns:
#
#   The address as an integer.
#
#-----------------------------------------------------------------------------------------------------------------------

def parse_address ( value, input_radix = 16, paragraph = 16 ):

    # Reject booleans explicitly; bool is a subclass of int and must never be read as an address.

    if isinstance ( value, bool ):
        raise ValueError ( f"address must be a number or string, not bool: {value!r}" )

    # Integers are taken verbatim, as decimal.

    if isinstance ( value, int ):
        return value

    # Normalise to a trimmed string, then dispatch on its notation.

    text = str ( value ).strip ()

    if ':' in text:
        segment_text, offset_text = text.split ( ':', 1 )
        return int ( segment_text, 16 ) * paragraph + int ( offset_text, 16 )
    if text.startswith ( '$' ):
        return int ( text [ 1 : ], 16 )
    if text.lower ().startswith ( '0x' ):
        return int ( text, 16 )
    if text [ -1 : ].lower () == 'h':
        return int ( text [ : -1 ], 16 )

    # A bare numeral is read in the configured input radix.

    return int ( text, input_radix )


#-----------------------------------------------------------------------------------------------------------------------
# Function: parse_size
#
# Description:
#
#   Parse a size given as an integer or string. Strings accept a binary multiplier suffix ('2K', '64KB', '4M', '1GB')
#   and a hex ('$800' / '0x800' / '800h') or decimal base.
#
# Arguments:
#
#   value : The size as a JSON integer or string.
#
# Returns:
#
#   The size in bytes as an integer.
#
#-----------------------------------------------------------------------------------------------------------------------

def parse_size ( value ):

    # Integers are taken verbatim, as decimal.

    if isinstance ( value, int ):
        return value

    # Normalise the string, then split off any binary multiplier suffix.

    text       = str ( value ).strip ().upper ().replace ( ' ', '' )
    multiplier = 1
    for suffix, factor in ( ( 'GB', 1 << 30 ), ( 'MB', 1 << 20 ), ( 'KB', 1 << 10 ),
                            ( 'G', 1 << 30 ), ( 'M', 1 << 20 ), ( 'K', 1 << 10 ) ):
        if text.endswith ( suffix ):
            multiplier = factor
            text       = text [ : -len ( suffix ) ]
            break

    # Read the remaining base in hex or decimal, then apply the multiplier.

    if text.startswith ( '$' ):
        base = int ( text [ 1 : ], 16 )
    elif text.startswith ( '0X' ):
        base = int ( text, 16 )
    elif text.endswith ( 'H' ):
        base = int ( text [ : -1 ], 16 )
    else:
        base = int ( text, 10 )

    # Return the size in bytes to the caller.

    return base * multiplier


#-----------------------------------------------------------------------------------------------------------------------
# Function: hex_digits
#
# Description:
#
#   Format an integer as plain hexadecimal digits (no prefix or suffix) in the requested letter case.
#
# Arguments:
#
#   value    : The integer to format.
#   hex_case : 'upper' or 'lower' for the hex letter digits.
#
# Returns:
#
#   The hexadecimal digit string.
#
#-----------------------------------------------------------------------------------------------------------------------

def hex_digits ( value, hex_case ):

    # Format the value with upper- or lower-case hex digits.

    return format ( value, 'X' if hex_case == 'upper' else 'x' )


#-----------------------------------------------------------------------------------------------------------------------
# Function: auto_address_width
#
# Description:
#
#   Compute the natural digit width for the largest address in the map, so every gutter address pads to the same width.
#   The width depends on the address format: hex-based formats size to the hex digits of the largest address, segmented
#   sizes to the segment, decimal-padded to the decimal digits, and the free-form decimal/intel cases need no padding.
#
# Arguments:
#
#   address_format : The selected address presentation style.
#   max_address    : The largest address appearing in the map.
#   hex_case       : 'upper' or 'lower' for the hex letter digits.
#
# Returns:
#
#   The digit width to pad addresses to, or 0 when no padding is needed.
#
#-----------------------------------------------------------------------------------------------------------------------

def auto_address_width ( address_format, max_address, hex_case ):

    # Hex-based formats size to the hex digits of the largest address.

    if address_format in ( 'commodore', 'c', 'intel', 'plain' ):
        return len ( hex_digits ( max_address, hex_case ) )

    # Segmented sizes to its segment; decimal-padded to its decimal digits.

    if address_format == 'segmented':
        return max ( 1, len ( hex_digits ( max_address // 16, hex_case ) ) )
    if address_format == 'decimal-padded':
        return len ( str ( max_address ) )

    # Free-form formats need no padding.

    return 0


#-----------------------------------------------------------------------------------------------------------------------
# Function: format_address
#
# Description:
#
#   Format an integer address according to the selected presentation style: 'commodore' ($XXXX), 'c' (0xXXXX), 'intel'
#   (XXXXh, guarded with a leading zero when it would start with a letter), 'plain' (bare hex), 'segmented'
#   (SSSS:OOOO), 'decimal', or 'decimal-padded'. The result is zero-padded to width where the style calls for it.
#
# Arguments:
#
#   address        : The integer address to format, or None for a blank gutter.
#   address_format : The selected address presentation style.
#   width          : The digit width to pad to.
#   hex_case       : 'upper' or 'lower' for the hex letter digits.
#   paragraph      : Bytes per segment, used to split a segmented address.
#
# Returns:
#
#   The formatted address string, or '' when address is None.
#
#-----------------------------------------------------------------------------------------------------------------------

def format_address ( address, address_format, width, hex_case, paragraph ):

    # A missing address renders as an empty gutter.

    if address is None:
        return ''

    # Build the zero-padded hex digit string shared by the hex-based styles.

    digits = hex_digits ( address, hex_case )
    if width and len ( digits ) < width:
        digits = digits.rjust ( width, '0' )

    # Decorate the digits according to the selected style.

    if address_format == 'commodore':
        return '$' + digits
    if address_format == 'c':
        return '0x' + digits
    if address_format == 'intel':
        guarded = ( '0' + digits ) if digits [ : 1 ].lower () in 'abcdef' else digits
        return guarded + 'h'
    if address_format == 'plain':
        return digits
    if address_format == 'segmented':
        segment_width = width or 4
        segment       = hex_digits ( address // paragraph, hex_case ).rjust ( segment_width, '0' )
        offset        = hex_digits ( address % paragraph, hex_case ).rjust ( segment_width, '0' )
        return f"{segment}:{offset}"
    if address_format == 'decimal':
        return str ( address )
    if address_format == 'decimal-padded':
        return str ( address ).rjust ( width or 0, '0' )

    # Fall back to the bare digits for any unrecognised style.

    return digits


#-----------------------------------------------------------------------------------------------------------------------
# Function: human_size
#
# Description:
#
#   Render a byte count as a compact human-readable size, choosing GB / MB / KB whole units where the value divides
#   evenly and a one-decimal value otherwise, falling back to bytes below 1 KB.
#
# Arguments:
#
#   byte_count : The size in bytes.
#
# Returns:
#
#   The human-readable size string (e.g. '2 KB', '1.5 MB', '512 B').
#
#-----------------------------------------------------------------------------------------------------------------------

def human_size ( byte_count ):

    # Pick the largest unit the value reaches, preferring whole units over a one-decimal value.

    for unit, factor in ( ( 'GB', 1 << 30 ), ( 'MB', 1 << 20 ), ( 'KB', 1 << 10 ) ):
        if byte_count >= factor:
            if byte_count % factor == 0:
                return f"{byte_count // factor} {unit}"
            return f"{byte_count / factor:.1f} {unit}"

    # Anything below 1 KB is reported in bytes.

    return f"{byte_count} B"


#-----------------------------------------------------------------------------------------------------------------------
# Class: Block
#
# Description:
#
#   One contiguous region of the memory map. A block carries its label and optional description lines (drawn inside the
#   box), its outside comments (drawn to the right), its start and inclusive end addresses, an optional forced body-row
#   count, and the derived size and body-row count filled in during layout.
#
# Attributes:
#
#   label       : The region name, drawn on the first body row.
#   start       : The start address (inclusive, low-address edge).
#   end         : The inclusive end address (last byte), or None when unknown.
#   description : Extra inside-the-box lines drawn below the label.
#   comments    : Outside-the-box notes; the first is arrow-anchored, the rest align beneath.
#   rows        : A forced body-row count, or None to let layout decide.
#   is_gap      : True for an auto-generated gap block spanning an unmapped range.
#   size        : The derived size in bytes, or None when it cannot be computed.
#   body_rows   : The decided body-row count, filled in during height assignment.
#-----------------------------------------------------------------------------------------------------------------------

class Block:

    #-------------------------------------------------------------------------------------------------------------------
    # Function: __init__
    #
    # Description:
    #
    #   Construct a block from its parsed fields, normalising description and comments to lists and defaulting the
    #   derived size and body-row count.
    #
    # Arguments:
    #
    #   label       : The region name.
    #   start       : The start address (inclusive).
    #   end         : The inclusive end address, or None.
    #   description : Inside-the-box description line(s), or None.
    #   comments    : Outside-the-box note(s), or None.
    #   rows        : A forced body-row count, or None.
    #   is_gap      : True for an auto-generated gap block.
    #
    # Returns:
    #
    #   None.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def __init__ ( self, label, start, end = None, description = None,
                   comments = None, rows = None, is_gap = False ):

        # Store the block's fields, normalising description and comments to lists.

        self.label       = label
        self.start       = start
        self.end         = end
        self.description = list ( description ) if description else []
        self.comments    = list ( comments ) if comments else []
        self.rows        = rows
        self.is_gap      = is_gap
        self.size        = None
        self.body_rows   = 1

    #-------------------------------------------------------------------------------------------------------------------
    # Function: inside_lines
    #
    # Description:
    #
    #   The text lines that sit inside the box: the label followed by any description lines.
    #
    # Arguments:
    #
    #   None.
    #
    # Returns:
    #
    #   The list of inside-the-box text lines.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def inside_lines ( self ):

        # Return the label followed by its description lines.

        return [ self.label ] + self.description


#-----------------------------------------------------------------------------------------------------------------------
# Function: build_blocks
#
# Description:
#
#   Parse the raw JSON blocks into a Block list sorted by start address, with each block's end and size resolved. An
#   explicit 'end' wins; otherwise 'size' derives the end; otherwise a missing end is inferred from the next block's
#   start. Sizes are computed once the ends are known.
#
# Arguments:
#
#   raw_blocks : The list of raw block dictionaries from the JSON.
#   config     : The merged rendering configuration.
#
# Returns:
#
#   The sorted list of Block objects with derived ends and sizes.
#
#-----------------------------------------------------------------------------------------------------------------------

def build_blocks ( raw_blocks, config ):

    # Select the radix for bare numeral strings, then parse every raw block.

    radix  = 16 if config [ 'input_radix' ] == 'hex' else 10
    blocks = []

    for entry in raw_blocks:

        # Every block must carry a start address; resolve the end from 'end' or 'size' when given.

        if 'start' not in entry:
            raise ValueError ( f"block is missing required 'start': {entry!r}" )
        start = parse_address ( entry [ 'start' ], radix, config [ 'paragraph' ] )
        end   = None
        if entry.get ( 'end' ) is not None:
            end = parse_address ( entry [ 'end' ], radix, config [ 'paragraph' ] )
        elif entry.get ( 'size' ) is not None:
            end = start + parse_size ( entry [ 'size' ] ) - 1

        # Normalise the inside description and outside comments to lists.

        description = entry.get ( 'description' )
        if isinstance ( description, str ):
            description = [ description ]
        comments = entry.get ( 'comments', entry.get ( 'comment' ) )
        if isinstance ( comments, str ):
            comments = [ comments ]

        blocks.append ( Block (
            label       = str ( entry.get ( 'label', '' ) ),
            start       = start,
            end         = end,
            description = description,
            comments    = comments,
            rows        = entry.get ( 'rows' ),
        ) )

    blocks.sort ( key = lambda block: block.start )

    # Infer any missing end addresses from the next block, then derive sizes.

    for index, block in enumerate ( blocks ):
        if block.end is None and index < len ( blocks ) - 1:
            block.end = blocks [ index + 1 ].start - 1
        if block.end is not None and block.end >= block.start:
            block.size = block.end - block.start + 1

    # Return the prepared block list to the caller.

    return blocks


#-----------------------------------------------------------------------------------------------------------------------
# Function: insert_gaps
#
# Description:
#
#   Return a new block list with explicit gap blocks inserted for unmapped ranges between consecutive blocks. When
#   --show-gaps is off the input list is returned unchanged.
#
# Arguments:
#
#   blocks : The sorted list of Block objects.
#   config : The merged rendering configuration.
#
# Returns:
#
#   The block list, augmented with gap blocks when --show-gaps is on.
#
#-----------------------------------------------------------------------------------------------------------------------

def insert_gaps ( blocks, config ):

    # With gaps disabled, hand back the original list untouched.

    if not config [ 'show_gaps' ]:
        return blocks

    # Walk the blocks, emitting a gap block wherever a block starts above the previous block's end + 1.

    augmented = []
    for index, block in enumerate ( blocks ):
        if index > 0:
            previous = blocks [ index - 1 ]
            if previous.end is not None and block.start > previous.end + 1:
                gap = Block (
                    label  = config [ 'gap_label' ],
                    start  = previous.end + 1,
                    end    = block.start - 1,
                    is_gap = True,
                )
                gap.size = gap.end - gap.start + 1
                augmented.append ( gap )
        augmented.append ( block )

    # Return the gap-augmented block list to the caller.

    return augmented


#-----------------------------------------------------------------------------------------------------------------------
# Function: scaled_rows
#
# Description:
#
#   Map a block size to a visual row count using the configured taper (log, sqrt, or linear). The size is normalised
#   between the smallest and largest sized blocks, then mapped across the [min_rows, max_rows] range. Degenerate cases
#   (no size, a single size class) collapse to min_rows.
#
# Arguments:
#
#   size     : The block's size in bytes, or None.
#   size_min : The smallest block size in the map.
#   size_max : The largest block size in the map.
#   config   : The merged rendering configuration.
#
# Returns:
#
#   The visual body-row count for the block.
#
#-----------------------------------------------------------------------------------------------------------------------

def scaled_rows ( size, size_min, size_max, config ):

    # A missing size or a single size class collapses to the minimum height.

    min_rows = config [ 'min_rows' ]
    max_rows = config [ 'max_rows' ]
    if size is None or size <= 0 or size_max <= size_min:
        return min_rows

    # Normalise the size between the smallest and largest blocks under the chosen taper.

    mode = config [ 'scale_mode' ]
    if mode == 'log':
        numerator   = math.log2 ( size ) - math.log2 ( size_min )
        denominator = math.log2 ( size_max ) - math.log2 ( size_min )
    elif mode == 'sqrt':
        numerator   = math.sqrt ( size ) - math.sqrt ( size_min )
        denominator = math.sqrt ( size_max ) - math.sqrt ( size_min )
    else:
        numerator   = size - size_min  # linear
        denominator = size_max - size_min

    # Map the normalised fraction across the [min_rows, max_rows] range.

    fraction = numerator / denominator if denominator else 0.0
    return int ( round ( min_rows + fraction * ( max_rows - min_rows ) ) )


#-----------------------------------------------------------------------------------------------------------------------
# Function: apply_show_size
#
# Description:
#
#   Append a human-readable size line inside each sized, non-gap block when --show-size is on. Does nothing when the
#   flag is off.
#
# Arguments:
#
#   blocks : The list of Block objects.
#   config : The merged rendering configuration.
#
# Returns:
#
#   None.
#
#-----------------------------------------------------------------------------------------------------------------------

def apply_show_size ( blocks, config ):

    # Nothing to do unless the size annotation was requested.

    if not config [ 'show_size' ]:
        return

    # Append a size line inside every sized, non-gap block.

    for block in blocks:
        if block.size and not block.is_gap:
            block.description = block.description + [ f"({human_size( block.size )})" ]


#-----------------------------------------------------------------------------------------------------------------------
# Function: assign_heights
#
# Description:
#
#   Decide the body-row count of every block. A block is at least as tall as its content (inside lines or comments); a
#   forced 'rows' count or the size-proportional scaling (when enabled) can make it taller, but never shorter than its
#   content.
#
# Arguments:
#
#   blocks : The list of Block objects.
#   config : The merged rendering configuration.
#
# Returns:
#
#   None.
#
#-----------------------------------------------------------------------------------------------------------------------

def assign_heights ( blocks, config ):

    # Establish the size range used to scale block heights.

    known_sizes = [ block.size for block in blocks if block.size and block.size > 0 ]
    size_min    = min ( known_sizes ) if known_sizes else 0
    size_max    = max ( known_sizes ) if known_sizes else 0

    # Each block is at least its content height, raised by a forced count or by size scaling.

    for block in blocks:
        content_rows = max ( 1, len ( block.inside_lines () ), len ( block.comments ) )
        if block.rows is not None:
            block.body_rows = max ( content_rows, int ( block.rows ) )
        elif config [ 'scale' ]:
            visual          = scaled_rows ( block.size, size_min, size_max, config )
            block.body_rows = max ( content_rows, visual )
        else:
            block.body_rows = content_rows


#-----------------------------------------------------------------------------------------------------------------------
# Class: MemoryMapRenderer
#
# Description:
#
#   Assemble the final ASCII memory map from prepared blocks. The renderer resolves the box style, comment arrow,
#   address digit width, interior box width, and gutter width up front, then draws boundaries and bodies in the
#   configured origin direction.
#
# Attributes:
#
#   blocks   : The prepared list of Block objects.
#   config   : The merged rendering configuration.
#   style    : The resolved box-drawing glyph set.
#   arrow    : The resolved outside-comment arrow.
#   width    : The address digit width.
#   interior : The interior box width in characters.
#   gutter   : The gutter width in characters.
#-----------------------------------------------------------------------------------------------------------------------

class MemoryMapRenderer:

    #-------------------------------------------------------------------------------------------------------------------
    # Function: __init__
    #
    # Description:
    #
    #   Resolve the box style, comment arrow, address digit width, interior box width, and gutter width from the blocks
    #   and configuration, caching them for the render pass.
    #
    # Arguments:
    #
    #   blocks : The prepared list of Block objects.
    #   config : The merged rendering configuration.
    #
    # Returns:
    #
    #   None.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def __init__ ( self, blocks, config ):

        # Resolve the glyph set and the outside-comment arrow.

        self.blocks = blocks
        self.config = config
        self.style  = BOX_STYLES [ config [ 'style' ] ]
        self.arrow  = config [ 'comment_arrow' ] or DEFAULT_ARROW [ config [ 'style' ] ]

        # Size the address gutter from the largest address, then the interior and gutter widths.

        max_address = max ( ( block.end or block.start ) for block in blocks )
        self.width = config [ 'address_width' ] or auto_address_width (
            config [ 'address_format' ], max_address, config [ 'hex_case' ] )

        self.interior = self._interior_width ()
        self.gutter   = self._gutter_width ()

    #-------------------------------------------------------------------------------------------------------------------
    # Function: _interior_width
    #
    # Description:
    #
    #   Compute the interior box width: the longest inside line plus one space of padding each side, honouring an
    #   explicit --width override and a minimum of 12 columns.
    #
    # Arguments:
    #
    #   None.
    #
    # Returns:
    #
    #   The interior box width in characters.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def _interior_width ( self ):

        # Measure the longest inside line and add one space of padding on each side.

        longest = max (
            ( len ( line ) for block in self.blocks for line in block.inside_lines () ),
            default = 0,
        )
        needed = longest + 2  # one space of padding each side

        # An explicit --width sets a floor; otherwise keep a 12-column minimum.

        if self.config [ 'width' ] != 'auto':
            return max ( int ( self.config [ 'width' ] ), needed )
        return max ( needed, 12 )

    #-------------------------------------------------------------------------------------------------------------------
    # Function: _displayed_addresses
    #
    # Description:
    #
    #   The set of addresses that appear in the gutter: every block's start, plus the final block's end + 1 when
    #   --show-end is on.
    #
    # Arguments:
    #
    #   None.
    #
    # Returns:
    #
    #   The list of integer addresses shown in the gutter.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def _displayed_addresses ( self ):

        # Collect every block start, adding the closing end address when --show-end is on.

        addresses = [ block.start for block in self.blocks ]
        if self.config [ 'show_end' ]:
            last = self.blocks [ -1 ]
            if last.end is not None:
                addresses.append ( last.end + 1 )
        return addresses

    #-------------------------------------------------------------------------------------------------------------------
    # Function: _gutter_width
    #
    # Description:
    #
    #   Compute the gutter width as the widest formatted address among the displayed addresses.
    #
    # Arguments:
    #
    #   None.
    #
    # Returns:
    #
    #   The gutter width in characters.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def _gutter_width ( self ):

        # Return the width of the widest formatted gutter address.

        return max (
            ( len ( self._format ( address ) ) for address in self._displayed_addresses () ),
            default = 0,
        )

    #-------------------------------------------------------------------------------------------------------------------
    # Function: _format
    #
    # Description:
    #
    #   Format a single address with the renderer's resolved address format, width, hex case, and paragraph size.
    #
    # Arguments:
    #
    #   address : The integer address to format.
    #
    # Returns:
    #
    #   The formatted address string.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def _format ( self, address ):

        # Delegate to format_address with the renderer's resolved settings.

        return format_address (
            address, self.config [ 'address_format' ], self.width,
            self.config [ 'hex_case' ], self.config [ 'paragraph' ] )

    #-------------------------------------------------------------------------------------------------------------------
    # Function: _gutter
    #
    # Description:
    #
    #   Build the left gutter cell for one boundary: a leading space, the right-justified formatted address (blank when
    #   None), and two trailing spaces before the box edge.
    #
    # Arguments:
    #
    #   address : The integer address to show, or None for a blank gutter.
    #
    # Returns:
    #
    #   The gutter cell string.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def _gutter ( self, address ):

        # Right-justify the formatted address within the gutter, padding with spaces.

        text = self._format ( address ) if address is not None else ''
        return ' ' + text.rjust ( self.gutter ) + '  '

    #-------------------------------------------------------------------------------------------------------------------
    # Function: _boundary
    #
    # Description:
    #
    #   Build one horizontal boundary line (top, mid, or bottom) at the given address, choosing the matching corner /
    #   tee glyphs and trimming trailing whitespace.
    #
    # Arguments:
    #
    #   address  : The integer address to show in the gutter, or None.
    #   position : 'top', 'mid', or 'bot' to pick the corner / tee glyphs.
    #
    # Returns:
    #
    #   The boundary line string.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def _boundary ( self, address, position ):

        # Pick the corner / tee glyphs for this boundary position, then draw the bar.

        corners = { 'top': ( self.style [ 'tl' ], self.style [ 'tr' ] ),
                    'mid': ( self.style [ 'ml' ], self.style [ 'mr' ] ),
                    'bot': ( self.style [ 'bl' ], self.style [ 'br' ] ) } [ position ]
        bar = corners [ 0 ] + self.style [ 'h' ] * self.interior + corners [ 1 ]
        return ( self._gutter ( address ) + bar ).rstrip ()

    #-------------------------------------------------------------------------------------------------------------------
    # Function: _body
    #
    # Description:
    #
    #   Build the body rows of one block: each row carries a blank gutter, the box verticals, the inside text (label
    #   then description, left-justified), and any outside comment. The first comment row is arrow-anchored; later rows
    #   align beneath it without an arrow.
    #
    # Arguments:
    #
    #   block : The Block to render the body of.
    #
    # Returns:
    #
    #   The list of body-row strings.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def _body ( self, block ):

        # Resolve the inside lines, the outside comments, and the blank gutter / arrow padding.

        lines        = []
        inside       = block.inside_lines ()
        comments     = block.comments if self.config [ 'show_comments' ] else []
        blank_gutter = ' ' + ' ' * self.gutter + '  '
        arrow_pad    = ' ' * len ( self.arrow )

        # Emit each body row, attaching its outside comment with an arrow on the first row only.

        for row in range ( block.body_rows ):
            inside_text = inside [ row ] if row < len ( inside ) else ''
            cell        = ( ' ' + inside_text ).ljust ( self.interior )
            line        = blank_gutter + self.style [ 'v' ] + cell + self.style [ 'v' ]
            if row < len ( comments ):
                connector = self.arrow if row == 0 else arrow_pad
                line += ' ' + connector + ' ' + comments [ row ]
            lines.append ( line.rstrip () )
        return lines

    #-------------------------------------------------------------------------------------------------------------------
    # Function: render
    #
    # Description:
    #
    #   Assemble the full memory map: an optional title, then the boundaries and block bodies. With origin 'top' the
    #   low address is at the top and addresses increase downward; with origin 'bottom' the order is reversed. The
    #   gutter address on each divider is the start of the block it opens.
    #
    # Arguments:
    #
    #   None.
    #
    # Returns:
    #
    #   The rendered memory map as a single newline-joined string.
    #
    #-------------------------------------------------------------------------------------------------------------------

    def render ( self ):

        # Emit the optional title above the map.

        lines = []
        if self.config [ 'title' ]:
            lines.append ( self.config [ 'title' ] )
            lines.append ( '' )

        blocks = self.blocks
        if self.config [ 'origin' ] == 'top':

            # Origin 'top': low address at the top, dividers carrying the next block's start.

            lines.append ( self._boundary ( blocks [ 0 ].start, 'top' ) )
            for index, block in enumerate ( blocks ):
                lines.extend ( self._body ( block ) )
                if index < len ( blocks ) - 1:
                    lines.append ( self._boundary ( blocks [ index + 1 ].start, 'mid' ) )
                else:
                    end_address = ( block.end + 1 ) if ( self.config [ 'show_end' ] and block.end is not None ) else None
                    lines.append ( self._boundary ( end_address, 'bot' ) )
        else:

            # Origin 'bottom': low address at the bottom, blocks drawn from the highest down.

            last        = blocks [ -1 ]
            top_address = ( last.end + 1 ) if ( self.config [ 'show_end' ] and last.end is not None ) else None
            lines.append ( self._boundary ( top_address, 'top' ) )
            for index in range ( len ( blocks ) - 1, -1, -1 ):
                lines.extend ( self._body ( blocks [ index ] ) )
                position = 'bot' if index == 0 else 'mid'
                lines.append ( self._boundary ( blocks [ index ].start, position ) )

        # Return the assembled map to the caller.

        return '\n'.join ( lines )


#-----------------------------------------------------------------------------------------------------------------------
# Function: build_config
#
# Description:
#
#   Merge the rendering configuration from three layers of increasing precedence: the built-in DEFAULTS, the JSON
#   'render' block, and the explicit CLI overrides. The store-true switches and the on/off scale flag are folded in,
#   and the title falls back to the JSON 'title' when none was given.
#
# Arguments:
#
#   data : The parsed JSON document.
#   args : The parsed command-line arguments.
#
# Returns:
#
#   The merged configuration dictionary.
#
#-----------------------------------------------------------------------------------------------------------------------

def build_config ( data, args ):

    # Start from the defaults, then layer the JSON 'render' block on top.

    config = dict ( DEFAULTS )
    config.update ( data.get ( 'render', {} ) )

    # Apply each value-bearing CLI flag, which overrides the JSON and the defaults.

    overrides = {
        'address_format': args.address_format,
        'address_width': args.address_width,
        'input_radix': args.input_radix,
        'hex_case': args.hex_case,
        'origin': args.origin,
        'scale_mode': args.scale_mode,
        'min_rows': args.min_rows,
        'max_rows': args.max_rows,
        'style': args.style,
        'width': args.width,
        'comment_arrow': args.comment_arrow,
        'gap_label': args.gap_label,
        'paragraph': args.paragraph,
        'title': args.title,
    }
    for key, value in overrides.items ():
        if value is not None:
            config [ key ] = value

    # Fold in the on/off scale flag and the store-true switches.

    if args.scale is not None:
        config [ 'scale' ] = ( args.scale == 'on' )
    if args.no_comments:
        config [ 'show_comments' ] = False
    if args.show_size:
        config [ 'show_size' ] = True
    if args.show_end:
        config [ 'show_end' ] = True
    if args.show_gaps:
        config [ 'show_gaps' ] = True

    # Fall back to the JSON title when no title was supplied anywhere else.

    if args.title is None and config.get ( 'title' ) is None and data.get ( 'title' ):
        config [ 'title' ] = data [ 'title' ]

    # Return the merged configuration to the caller.

    return config


#-----------------------------------------------------------------------------------------------------------------------
# Function: parse_arguments
#
# Description:
#
#   Build the command-line argument parser and parse argv into a namespace. The --width option is post-validated to be
#   either the literal 'auto' or an integer.
#
# Arguments:
#
#   argv : The argument list to parse (without the program name).
#
# Returns:
#
#   The parsed argparse namespace.
#
#-----------------------------------------------------------------------------------------------------------------------

def parse_arguments ( argv ):

    # Define every flag the renderer accepts.

    parser = argparse.ArgumentParser ( description = 'Render an ASCII memory map from JSON.' )
    parser.add_argument ( 'json_file', nargs = '?', help = 'Path to the memory-map JSON file.' )
    parser.add_argument ( '--file', dest = 'file', help = 'Path to the memory-map JSON file.' )
    parser.add_argument (
        '--address-format',
        choices = [ 'commodore', 'c', 'intel', 'plain', 'segmented', 'decimal', 'decimal-padded' ]
    )
    parser.add_argument ( '--address-width', type = int )
    parser.add_argument ( '--input-radix', choices = [ 'hex', 'decimal' ] )
    parser.add_argument ( '--hex-case', choices = [ 'upper', 'lower' ] )
    parser.add_argument ( '--origin', choices = [ 'top', 'bottom' ] )
    parser.add_argument ( '--scale', choices = [ 'on', 'off' ] )
    parser.add_argument ( '--scale-mode', choices = [ 'log', 'linear', 'sqrt' ] )
    parser.add_argument ( '--min-rows', type = int )
    parser.add_argument ( '--max-rows', type = int )
    parser.add_argument ( '--style', choices = [ 'unicode', 'heavy', 'double', 'ascii' ] )
    parser.add_argument ( '--width', help = "Interior box width: 'auto' or an integer." )
    parser.add_argument ( '--comment-arrow' )
    parser.add_argument ( '--no-comments', action = 'store_true' )
    parser.add_argument ( '--show-size', action = 'store_true' )
    parser.add_argument ( '--show-end', action = 'store_true' )
    parser.add_argument ( '--show-gaps', action = 'store_true' )
    parser.add_argument ( '--gap-label' )
    parser.add_argument ( '--paragraph', type = int )
    parser.add_argument ( '--title' )
    args = parser.parse_args ( argv )

    # Post-validate --width as either the literal 'auto' or an integer.

    if args.width is not None and args.width != 'auto':
        try:
            args.width = int ( args.width )
        except ValueError:
            parser.error ( "--width must be 'auto' or an integer" )
    return args


#-----------------------------------------------------------------------------------------------------------------------
# Function: main
#
# Description:
#
#   Command-line entry point. Forces UTF-8 output for the box-drawing glyphs, parses arguments, loads and validates the
#   JSON, then builds, lays out, and renders the memory map. Returns a process exit code: 0 on success, 1 on an input
#   or rendering error, 2 when no JSON file was given.
#
# Arguments:
#
#   argv : The argument list (without the program name).
#
# Returns:
#
#   The process exit code (0 success, 1 input/render error, 2 usage error).
#
#-----------------------------------------------------------------------------------------------------------------------

def main ( argv ):

    # Box-drawing and arrow glyphs are non-ASCII; force UTF-8 output so the map
    # renders correctly on consoles that default to a legacy code page (Windows).

    try:
        sys.stdout.reconfigure ( encoding = 'utf-8' )
    except ( AttributeError, ValueError ):
        pass

    # Resolve the input path from the positional argument or --file.

    args = parse_arguments ( argv )
    path = args.file or args.json_file
    if not path:
        sys.stderr.write ( "error: no JSON file given (pass a path or --file)\n" )
        return 2

    # Load and parse the JSON document, reporting read and decode errors.

    try:
        with open ( path, encoding = 'utf-8' ) as handle:
            data = json.load ( handle )
    except OSError as error:
        sys.stderr.write ( f"error: cannot read {path}: {error}\n" )
        return 1
    except json.JSONDecodeError as error:
        sys.stderr.write ( f"error: invalid JSON in {path}: {error}\n" )
        return 1

    # A map must carry at least one block.

    raw_blocks = data.get ( 'blocks' )
    if not raw_blocks:
        sys.stderr.write ( "error: JSON has no 'blocks' array\n" )
        return 1

    # Build the config, lay the blocks out, and render, reporting data errors.

    try:
        config = build_config ( data, args )
        blocks = build_blocks ( raw_blocks, config )
        blocks = insert_gaps ( blocks, config )
        apply_show_size ( blocks, config )
        assign_heights ( blocks, config )
        output = MemoryMapRenderer ( blocks, config ).render ()
    except ( ValueError, KeyError ) as error:
        sys.stderr.write ( f"error: {error}\n" )
        return 1

    # Emit the rendered map and report success.

    print ( output )
    return 0


#-----------------------------------------------------------------------------------------------------------------------
# Program Entry Point
#-----------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    sys.exit ( main ( sys.argv [ 1 : ] ) )
