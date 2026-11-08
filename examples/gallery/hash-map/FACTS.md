# How a hash map finds a key: facts

Every claim comes from here. Python references fetched from docs.python.org (the only web access used).

## Python's own behaviour

- [SOURCE] hash() returns an integer hash value for an object; dictionaries use these values to quickly compare keys during a lookup. — https://docs.python.org/3/library/functions.html#hash
- [SOURCE] An object is hashable if it has a hash value that never changes during its lifetime and can be compared to other objects; hashable objects that compare equal must have the same hash value. — https://docs.python.org/3/glossary.html#term-hashable
- [SOURCE] Hashability makes an object usable as a dictionary key and set member, because these structures use the hash value internally. — https://docs.python.org/3/glossary.html#term-hashable
- [SOURCE] Immutable sequences such as tuples can be used as dict keys; hashing a tuple that contains unhashable values raises TypeError. — https://docs.python.org/3/library/stdtypes.html#immutable-sequence-types

## General computer science

- [EXTERNAL] Searching an unsorted list means checking items one at a time, so the worst case is as many looks as there are items. — Cormen et al., Introduction to Algorithms, chapter 11 (Hash tables) intro, and the linear search entry in any algorithms text.
- [EXTERNAL] A hash table turns the hash value into a slot number (a common way is the remainder after dividing by the number of slots) and goes straight to that slot. — Cormen et al., Introduction to Algorithms, chapter 11, "hash functions: the division method".
- [EXTERNAL] Two different keys can hash to the same slot (a collision); hash tables have several ways to handle this, and they compare the keys to tell the entries apart. — Cormen et al., chapter 11, "collision resolution".

## Invented example (marked on screen as an example)

- Keys (fruit names), the values (3 for plum), the hash number 7401935 and the eight-box shelf are invented. 7401935 mod 8 = 7 (checked by hand: 8 x 925241 = 7401928, remainder 7). Python's real hash of a string differs between runs.

## What the video does not claim

- How CPython lays out its table inside (open addressing, resizing): not said.
- Timings or "constant time" as a number: not said; the video says "one look".
