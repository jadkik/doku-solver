doku-solver
===========

Mathdoku and Sudoku Solver

What are those games?
=====================

 * [Sudoku](https://en.wikipedia.org/wiki/Sudoku) is too well known to be presented.
 * [MathDoku](https://en.wikipedia.org/wiki/Mathdoku) (also known as KenKen) is a game similar to Sudoku, but with different rules involving maths.
 
Why one solver for both?
========================

I had made a Sudoku solver, with the rules incorporated inside the solving algorithm.
When I heard of MathDoku (via [F-Droid](http://f-droid.org/posts/mathdoku/)),
I could not do the same because there are different rules.

This resulted in a "group" system, and a "condition" system.
A subset of those rules, made solving sudoku grids easier.

How can I solve a grid?
=======================

Run `python main.py`. You will be provided with a list of grids.
Write just enough to uniquely identify its name, and there you go.
It will ask you for `DO_LOG`. If you say yes, it will show a log of
what's happening. Then, keep saying "yes" to run again, until you see
your grid solved.

I want to solve my own grids. How can I do it?
==============================================

Sure! There's a file for that, it's called `input.py`.
It will ask for some info when you run it.

First, the size. It assumes all grids are square.
If it's a 4x4 mathdoku grid enter `4`, for example.
If it's a sudoku grid, enter `sudoku`. It will create a 9x9 grid,
and simplify your input process (3 square groups, unique conditions, ...).

Now, if it's a sudoku grid. It will ask for a cell's value and it's
coordinates. So, first you are asked for a cell's value and then for
it's coordinates as `x,y`.
Example: `0,0` (yes, indexes are zero-based) for the first cell,
`2,1` for the cell in the third column on the second row, etc.

When you're done, leave the value empty and press enter.

If it's a mathdoku grid, it will ask you for a condition, which is
one of `=+-/*u`, preceded by a value. `u` is for unique (which you won't
use for MathDoku grids: rows and columns automatically abide by this law).
Example: `8+` means sums to 8, `2=` means equals to 2, etc.
After that, it will ask for the cell coordinates, also zero-based, like
for sudoku grids. Press enter when you're done adding cells.
NOTE: every cell should be in one "block" (a special kind of group), so
you will not be allowed to add the same cell twice or, not add a cell.

After using either of these methods, you will have a piece of code in
the terminal. You will have to put this at the end of the file called
`grids.py`, so that it can be detected by the solver.

How does it work?
=================

It divides the grid into groups. Some of them are blocks, rows, columns,
or just regular groups. Blocks are the main groups that subdivide
the grid, they do not share cells, or leave cells out of all of them.
Rows and columns are what they say they are. Other groups are just groups
of cells who have conditions.

Conditions are what builds the logic, and lets the solving take place.
Until now, you have:

 * Equality conditions: the cell its group contains equals this value.
 * Sum conditions: the cells its group contains must sum up to this value.
 * Product conditions: same as above.
 * Difference conditions: the cells its group contains must have a difference of this value (in one way or another)
 * Division conditions: same as above.
 * Unique conditions: the cells its group contains have exactly one of each value.

Each condition has a "processing method" to get to the answer, and each
time it gets closer, it subdivides its group into different groups,
or removes it.

Contributing
============

This is as far as I know in the solving techniques of the games.
The more I find techniques, the more I'll improve this. If you think of
anything let me know, and if you can write the code, do it!
