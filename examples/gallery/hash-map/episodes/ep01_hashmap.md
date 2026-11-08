# Script: How a hash map finds a key

About 128 spoken words. Estimate: 128/2.6 + 0.7 x 11 lines + 4 beats + 6 + 3 (one card) = about 70 s (actual 62 s).
Look and moves: DIRECTION.md (storyline A, the shelf).

## Cold open (before intro; the problem happening)
1. "To find plum on this shelf, you check every box, one by one." [8 big boxes; a rust frame hops box 0 to box 7; live counter "n looks"; "example data" note]
2. "Up to eight looks. For a thousand boxes, up to a thousand." [counter line]

## Intro (card=False)
3. "A Python dict does it in one look. How?" [title types in over the shelf] (beat)

## Chapter 1: A key becomes a number (iris from box 7; the one card, blur_in; shelf kept)
4. "Python turns the key into a number, with hash." [plum -> hash() -> 7401935, marked example]
5. "Divide by eight, the number of boxes. The remainder, seven, is plum's shelf." [7401935 mod 8 = 7, large; arrow to box 7] (beat)

## Chapter 2: Jump straight there (whip right; no card)
6. "To look up plum, do the same sum. Same key, same shelf." [d["plum"] -> hash, mod 8 -> 7]
7. "Go straight to box seven. One look, however long the shelf." [arrow down; the value rolls in with slot; example value] (beat)

## Chapter 3: Two keys, one shelf (flood from box 7; no card)
8. "Two keys can land on one shelf. The map keeps both and compares keys to tell them apart. A key must be hashable: its hash never changes." [fig and plum into box 7; fig ≠ plum, the ≠ takes the accent; "hashable"] (beat)

## Outro
9. Silent: the shelf returns to its opening place, plum lit, "1 look".
10. Answer over the shelf (outro keep=[shelf, "1 look"]): "A hash turns the key into a shelf number, so lookup jumps straight there."
11. End card: "Your dict is a shelf, and the key is its address." Narration: "Next time you read a dict, picture the shelf."

## Critique
1. Problem on screen in 20 s? yes, the scan and its counter.
2. One question, asked and answered in the same words? yes.
3. Promise and route? the intro promises "one look"; at a minute the route is the three chapters themselves.
4. Terms defined after the problem? yes: hash, remainder, hashable.
5. Chapters concrete, takeaway, beat? yes.
6. Bridges? the seams are the bridges (iris on the box, whip along the number's path, flood from the crowded box); the chapter 1 card is the only breath.
7. Running example the same? yes: plum, 7, eight boxes.
8. Ending solves the opening on the same objects? yes.
9. Recap? none (recap=[]).
10. A Next? yes, "picture the shelf".
11. Words and time in range? about 128 words, about 70 s.
