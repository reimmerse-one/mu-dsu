"""HTML viewer program (Listing 4 simplified)."""

VIEWER_PROGRAM = """\
var parsed_color = "red";
var parsed_size = 12;
var parsed_text = "Hello World";
set font color parsed_color;
set font size parsed_size;
print parsed_text;
"""

VIEWER_MULTI_PRINT = """\
var t1 = "First line";
var t2 = "Second line";
set font size 14;
set font color "blue";
print t1;
print t2;
"""
