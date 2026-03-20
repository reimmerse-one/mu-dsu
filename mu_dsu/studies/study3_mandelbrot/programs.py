"""Mandelbrot set calculation program (Listing 7 simplified)."""

# Small dimensions for fast tests
MANDELBROT_PROGRAM = """\
var MAX_ITER = 20;
var ZOOM = 100;
var HEIGHT = 5;
var WIDTH = 5;
var zx = 0;
var zy = 0;
var cX = 0;
var cY = 0;
var tmp = 0;
var iter = 0;
for (var y = 0; y < HEIGHT; ++y) {
    for (var x = 0; x < WIDTH; ++x) {
        zx = 0;
        zy = 0;
        cX = (x - 3) / ZOOM;
        cY = (y - 3) / ZOOM;
        iter = MAX_ITER;
        while (((zx * zx) + (zy * zy)) < 4 && iter > 0) {
            tmp = (zx * zx) - (zy * zy) + cX;
            zy = (2.0 * (zx * zy)) + cY;
            zx = tmp;
            iter = iter - 1;
        };
    };
};
"""

# Simple nested for — for testing for->parfor targeting
NESTED_FOR_SIMPLE = """\
var total = 0;
for (var i = 0; i < 3; ++i) {
    for (var j = 0; j < 4; ++j) {
        total = total + 1;
    };
};
"""
