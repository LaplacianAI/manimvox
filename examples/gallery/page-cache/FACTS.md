# Facts: Why is the same page faster the second time?

Web access used: learn.microsoft.com, aws.amazon.com/caching (fetched 2026-11-10).

## The cache and the route

- [EXTERNAL] Applications use a cache to improve performance for repeated access to information in a data store. — https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside
- [EXTERNAL] The application first tries to read the item from the cache. If it is not there (a cache miss), it gets the item from the data store, adds it to the cache and returns it. — same page, "Solution", steps 1 to 3
- [EXTERNAL] If the item is in the cache, the application returns it without going to the data store. — same page, example code: "If the cache contains a matching item, it returns the item."
- [EXTERNAL] A cache is "a high-speed data storage layer which stores a subset of data"; a cache hit means the data was present when fetched, a miss that it was not. — https://aws.amazon.com/caching/
- [EXTERNAL] "Memory is orders of magnitude faster than disk (magnetic or SSD)": the reason the cache is faster than a database that reads from disk. — https://aws.amazon.com/caching/ (Benefits of caching)

## What the video says and does not say

- It shows one common design (a cache between the app server and the database), marked on screen as such. Real sites differ, and browsers keep their own copies too; not covered.
- Speed is never given as a number.
- The part names and the four boxes are a generic example, not any company's system.
