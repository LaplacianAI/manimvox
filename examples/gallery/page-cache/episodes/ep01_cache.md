# Script: Why is the same page faster the second time?

About 110 spoken words; about 42 s of speech plus pauses and the answer; one chapter seam.

## Opening (cardless; the four parts already on screen)
1. "Why is the same page faster the second time?" [browser, app server, cache, database; the question types over them] (beat)

## Trip one (the first time)
2. "Open a page, and the request goes to the app server." [flow browser to app server; leader on the app server]
3. "It asks the cache first. A cache keeps recent answers, but this one is empty." [flow app to cache, nothing back; cache reads "empty"; leader on the cache]
4. "So it asks the database, which keeps everything and is slower." [flow app to database and back; leader on the database]
5. "It saves a copy in the cache, then sends the page." [violet flow app to cache, cache reads "a saved copy"; flow app to browser, the page leaves]

## Trip two (a pulse on the cache)
6. "Now open it again." [the cache pulses; the diagram stays]
7. "The app server asks the cache, and this time the answer is there." [flow app to cache and back; the database dims]
8. "The database is never asked, so the page comes back sooner." [flow app to browser]

## Ending
9. Answer: "The second time, the app server answers from its cache and skips the slow database." [same boxes, trip-two loop alive, database dim]

## Critique
1. Problem on screen in 20 s: the four parts and the question. 2. One question, answered in its words: yes. 3. Promise: the question; route: "first time, then again". 4. Terms once, after the need: cache (line 3), database (line 4). 5. Takeaways: line 5 and line 8. 6. Bridge: "Now open it again." 7. Same request in both trips. 8. Ending on the same boxes. 9. No recap. 10. no Next. 11. about 110 words, 1 to 2 chapters.
Flow check: line 3 (flow to cache, none back, empty) matches; line 4 (to db and back) matches; line 7 (cache and back, db dim) matches. The old version said the cache was asked but the flow skipped it; this one cannot.
