# How a hash map finds a key

## The question

Question: How does a dict find a key so fast?

Situation that shows it: a shelf of eight labelled boxes searched one by one, a counter ticking up to eight looks.

## The viewer

A beginner programmer who uses dicts daily and has never thought about how they work.

## The theme

Paper and ink: cream ground, ink text, one blue accent, rust only for the slow scan. See DIRECTION.md.

## Running example

Plum, whose example hash 7401935 gives shelf 7 of 8; fig lands on the same shelf. All invented, marked as an example on screen.

## Chapters

1. A key becomes a number: hash(), then the remainder after dividing by 8.
2. Jump straight there: the same sum on lookup, one look.
3. One shelf, two keys: collisions, and why a key must be hashable.
