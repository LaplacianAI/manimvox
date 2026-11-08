# Script v3: How a hash map finds a key

About 140 spoken words, one line right after another (0.3 s between lines), a 1 s beat only after the answer.
Estimate: 140 / 2.7 + 13 lines x 0.3 + 1 + 2.3 end card = about 60 s.

## Cold open
1. "To find plum on this shelf, you check every box, one by one." [8 big boxes; a rust frame hops 0 to 7; live "n looks"]
2. "Up to eight looks. For a thousand boxes, a thousand." [counter line]

## Intro (card=False, title types in over the shelf)
3. "A Python dict finds plum in one look. How?"

## Chapter 1 (iris from box 7, no card)
4. "First, Python turns the key into a number, with hash." [plum -> hash() -> 7401935 (example)]
5. "Divide by eight, the number of boxes. What's left over, seven, is plum's box." [7401935 = 8 x 925241 + 7, the 7 lit, small `% 8`; arrow into box 7]
6. "That is where plum lives, with its value." [box 7 reads "plum: 3"]

## Chapter 2 (whip right, no card)
7. "To look up plum, do the same sum. Same key, same box." [d["plum"] -> hash() -> 7 -> box 7]
8. "Go straight there. The value, three, comes out. One look, however long the shelf." [box lights; the 3 rises out to d["plum"]]

## Chapter 3 (flood from box 7, no card)
9. "Sometimes two keys land in the same box." [fig -> 7; box 7 grows, fig: 5 above plum: 3]
10. "The box keeps both, and checks which key you asked for." [d["plum"] arrives; a tick lands on plum]
11. "That is why a key can not change: its box would move." [plum becomes plums; the arrow swings to another box]. The shelf returns to its opening place, plum lit, "1 look", during this line.

## Outro
12. Answer over the shelf: "A hash turns the key into a shelf number, so lookup jumps straight there." (beat)
13. End card: "Your dict is a shelf, and the key is its address." Narration: "Next time you read a dict, picture the shelf."

## Critique
1. Problem in 20 s? yes, the scan and its counter. 2. One question, answered in the same words? yes. 3. Promise? "one look". 4. Terms after the problem? hash, left over (no "mod"), key's box. 5. Takeaway per chapter? 1: where plum lives. 2: one look. 3: the key can not change. 6. Seams are bridges: iris on plum's box, whip along the number's path, flood from the crowded box. 7. Same example everywhere: plum, 7, eight boxes, fig. 8. Ending on the same objects? yes. 9. No recap. 10. A Next: "picture the shelf". 11. About 140 words, about 60 s.
