# Motion patterns, runnable

Each example is the body of one chapter inside an episode's `build()`, after `self.intro(...)`. Paste it in, keep the `self.chapter(...)` line, and raise `NCHAP` by one. Every one runs against the kit with `from manimvox.kit import *` and uses no LaTeX. Positions keep to the safe stage, x from -6.6 to 6.6 and y from -3.45 to 3.15. The narration lines are placeholders; write your own.

## Contents

1. Carry an object between scenes
2. Reveal items as they are named
3. A table lit row by row
4. A graph drawn node by node
5. Before and after
6. Zoom into a box
7. A sequence diagram
8. Hub and spoke
9. Recipe: coloured words
10. Recipe: a plane without Axes
11. Recipe: a live number

## 1. Carry an object between scenes

Use when the same thing appears in two scenes and the viewer should see it is the same thing. `ReplacementTransform(a, b)` turns `a` into `b` and leaves `b` on stage. `self.clear()` would fade the carried object too, so fade the rest of the stage yourself and leave it. Note that `self.chapter(...)` calls `clear()`, so a carried object lives within one chapter.

```python
self.chapter("Carry an object", "A request arrives, and then we open it up.")
req = node("Request", "POST /runs", color=BLUE).move_to(LEFT * 4 + UP * 0.5)
self.say("A request arrives at the server.", FadeIn(req))

detail = card("Request", ["method: POST", "path: /runs", "body: a spec"], w=4.2, color=BLUE)
detail.move_to(LEFT * 3.6)
queue = card("Queue", ["waiting for a worker"], w=4.2, color=ORANGE).move_to(RIGHT * 3.4)
self.say("Open it, and it holds a method, a path and a body. Then it joins a queue.",
         ReplacementTransform(req, detail), FadeIn(queue), run_time=1.2)

# the next scene: everything but the carried card leaves, and it moves to its new place
rest = [m for m in self.stage() if m is not detail]
worker = card("Worker", ["takes the request", "runs the spec"], w=4.2, color=TEAL).move_to(RIGHT * 3.4)
self.say("A worker picks the same request up.",
         *[FadeOut(m) for m in rest], detail.animate.move_to(LEFT * 3.6 + DOWN * 0.3), FadeIn(worker))
```

## 2. Reveal items as they are named

Use when a line lists things. `steps` spreads the animations over the line, so each item appears as its word is spoken. Build the items first, then pass one animation per item in the order the line names them.

```python
self.chapter("Reveal as named", "Three steps, shown as each one is named.")
parse = card("Parse", ["read the bytes"], w=3.6, color=BLUE)
check = card("Check", ["is it valid"], w=3.6, color=VIOLET)
store = card("Store", ["write it down"], w=3.6, color=TEAL)
row = VGroup(parse, check, store).arrange(RIGHT, buff=0.6).move_to(ORIGIN)
self.steps("The server parses the request, checks it, and then stores it.",
           [FadeIn(parse, shift=UP * 0.3), FadeIn(check, shift=UP * 0.3), FadeIn(store, shift=UP * 0.3)])
```

## 3. A table lit row by row

Use when a table is read aloud one row at a time. Highlight with the row background's stroke. Never `Indicate` a row: it scales the filled panel and floods it. `rows[0]` is the header, and `row[0]` is a row's background.

```python
self.chapter("Table, row by row", "Each role gets its own row.")
rows = table([["Role", "Can read", "Can write"],
              ["viewer", "yes", "no"],
              ["editor", "yes", "yes"],
              ["owner", "yes", "yes"]], col_w=[3.0, 2.6, 2.6]).move_to(UP * 0.3)
self.say("Here are three roles and what each may do.", FadeIn(rows))

lit, prev = [], None
for row in rows[1:]:
    group = [row[0].animate.set_stroke(ACCENT, 3)]
    if prev is not None:
        group.append(prev[0].animate.set_stroke(LINE, 1))
    lit.append(group)
    prev = row
self.steps("A viewer can only read. An editor can read and write. An owner can do both.", lit)
```

## 4. A graph drawn node by node

Use for a dependency graph or any set of linked things. Position the `gnode`s first, because `gedge` is computed from where they are. Pass each node, with the edges it completes, as one step.

```python
self.chapter("Graph, node by node", "The graph grows as each part is named.")
api = gnode("api", BLUE).move_to(LEFT * 4.5 + UP * 0.4)
auth = gnode("auth", VIOLET).move_to(LEFT * 0.5 + UP * 1.6)
db = gnode("db", TEAL, shape="square").move_to(LEFT * 0.5 + DOWN * 1.6)
cache = gnode("cache", ORANGE, shape="square").move_to(RIGHT * 4.2 + DOWN * 0.4)
e_auth = gedge(api, auth, "calls")
e_db = gedge(api, db, "reads")
e_chk = gedge(auth, db, "looks up")
e_cache = gedge(db, cache, "fills")
self.steps("The api calls auth and reads the db. Auth looks things up in the db, and the db fills the cache.",
           [FadeIn(api),
            [FadeIn(auth), Create(e_auth)],
            [FadeIn(db), Create(e_db)],
            Create(e_chk),
            [FadeIn(cache), Create(e_cache)]])
```

## 5. Before and after

Use for a change: a number, a design, a result. Put the old state down, then `swap` it for the new one in the same place, so the eye stays put and only the content changes. `swap` is a play on its own, so run it inside `narrate`.

```python
self.chapter("Before and after", "Same request, two designs.")
before = stat("12 s", "per request, one at a time", ERROR, w=4.6).move_to(ORIGIN)
self.say("Before, each request waited for the one ahead of it.", FadeIn(before))
after = stat("0.4 s", "per request, in parallel", OK, w=4.6).move_to(ORIGIN)
with self.narrate("After the change, requests run side by side, and each takes under half a second."):
    self.swap(before, after)
```

## 6. Zoom into a box

Use when one part of a diagram deserves its own detail. Fade the other parts, scale the chosen box up and move it, then draw what is inside.

```python
self.chapter("Zoom into a box", "Now look inside the worker.")
nodes, arrows = flow(["Client", "Gateway", "Worker", "Store"], w=2.4)
VGroup(nodes, arrows).move_to(UP * 0.6)  # move both: the arrows are separate from the nodes
self.say("A request goes from the client through the gateway to a worker, and into the store.",
         FadeIn(nodes), Create(arrows))

target = nodes[2]
others = VGroup(*[m for m in nodes if m is not target], arrows)
inner, inner_arrows = flow(["Pull", "Run", "Report"], w=2.4, color=TEAL)
VGroup(inner, inner_arrows).move_to(DOWN * 1.6)
self.say("Zoom in on the worker. It pulls a job, runs it, and reports back.",
         FadeOut(others), target.animate.scale(1.5).move_to(UP * 1.4),
         FadeIn(inner), Create(inner_arrows), run_time=1.2)
```

## 7. A sequence diagram

Use for a conversation between parts. Lifelines are columns; each message is a row, top to bottom, in the order it happens. A reply is `dashed=True`. Reveal the columns first, then one message per step.

```python
self.chapter("Sequence diagram", "Who says what, in order.")
client = lifeline("Client", -4.2)
server = lifeline("Server", 0.0, color=VIOLET)
store = lifeline("Store", 4.2, color=TEAL)
m1 = message(client, server, 1.2, "POST /runs")
m2 = message(server, store, 0.3, "save")
m3 = message(store, server, -0.6, "ok", dashed=True)
m4 = message(server, client, -1.5, "202 accepted", dashed=True)
self.say("Three parts take part.", FadeIn(client), FadeIn(server), FadeIn(store))
self.steps("The client posts a run. The server saves it. The store confirms, and the server accepts.",
           [Create(m1), Create(m2), Create(m3), Create(m4)])
```

## 8. Hub and spoke

Use when one thing connects to many. Lines from the hub to a grid of cards cross the nearer cards, so send the lines behind with `set_z_index(-1)`: the opaque cards hide them.

```python
self.chapter("Hub and spoke", "One hub, six parts.")
hub = node("Gateway", "routes everything", w=2.6, color=ACCENT).move_to(LEFT * 4.2)
names = ["Auth", "Billing", "Search", "Mail", "Files", "Audit"]
cards = VGroup(*[card(n, w=3.0, color=BLUE) for n in names])
cards.arrange_in_grid(rows=3, cols=2, buff=(0.5, 0.35)).move_to(RIGHT * 2.4 + DOWN * 0.1)
spokes = VGroup(*[Line(hub.get_center(), c.get_center()).set_stroke(LINE, 2) for c in cards])
spokes.set_z_index(-1)
self.say("The gateway sits at the centre.", FadeIn(hub))
self.steps("It routes to auth, billing, search, mail, files and audit.",
           [[FadeIn(c), Create(s)] for c, s in zip(cards, spokes)])
```

## 9. Recipe: coloured words

`T()` colours a whole line. To colour single words, build the `Text` yourself and slice its glyphs. Turn ligatures off so one letter is one glyph, and check whether your Manim gives a space a glyph: the helper below counts both ways.

```python
self.chapter("Coloured words", "Colour only the word that matters.")


def colour_words(text, words, color, size=40):
    """A line of text with the given words in `color`."""
    line = Text(text, font=FONT, font_size=size, color=INK, disable_ligatures=True)
    spaced = len(line) == len(text)  # some Manim versions give a space a glyph, some do not
    for w in words:
        i = text.index(w)
        start, n = (i, len(w)) if spaced else (len(text[:i].replace(" ", "")), len(w.replace(" ", "")))
        line[start:start + n].set_color(color)
    return fit(line, 12.0, 1.0)


sentence = colour_words("Only the new word is accent coloured", ["new", "accent"], ACCENT)
sentence.move_to(UP * 0.5)
wrong = colour_words("A refused call is an error", ["refused", "error"], ERROR).move_to(DOWN * 1.0)
self.say("Only the new word takes the accent colour.", FadeIn(sentence))
self.say("A refusal is shown in the error colour.", FadeIn(wrong))
```

## 10. Recipe: a plane without Axes

`Axes` writes its numbers through LaTeX, which manimvox does not use. Draw the plane from `Line`s, a `DashedVMobject` circle and `Arrow`s, and label it with `T`.

```python
self.chapter("A plane without Axes", "A point on the unit circle.")
origin = np.array([0.0, -0.1, 0.0])
unit = 1.8
grid = VGroup(*[Line(origin + RIGHT * i * unit * 0.5 + DOWN * 2.2, origin + RIGHT * i * unit * 0.5 + UP * 2.2)
                for i in range(-4, 5)],
              *[Line(origin + UP * j * unit * 0.5 + LEFT * 3.7, origin + UP * j * unit * 0.5 + RIGHT * 3.7)
                for j in range(-2, 3)]).set_stroke(LINE, 1)
x_axis = Arrow(origin + LEFT * 3.7, origin + RIGHT * 3.7, buff=0, color=MUTED, stroke_width=3, tip_length=0.2)
y_axis = Arrow(origin + DOWN * 2.2, origin + UP * 2.2, buff=0, color=MUTED, stroke_width=3, tip_length=0.2)
ring = DashedVMobject(Circle(radius=unit, color=BLUE, stroke_width=3).move_to(origin), num_dashes=48)
ticks = VGroup(T("1", 20, MUTED).move_to(origin + RIGHT * unit + DOWN * 0.3 + RIGHT * 0.15),
               T("1", 20, MUTED).move_to(origin + UP * unit + LEFT * 0.3))
self.say("This is a plane: two axes and a circle of radius one.",
         Create(grid), Create(x_axis), Create(y_axis), Create(ring), FadeIn(ticks), run_time=1.4)

tip = origin + unit * np.array([np.cos(PI / 4), np.sin(PI / 4), 0])
vec = Arrow(origin, tip, buff=0, color=ACCENT, stroke_width=5)
dot = Dot(tip, color=ACCENT)
tag = T("(cos θ, sin θ)", 22, ACCENT).next_to(dot, UR, buff=0.12)
self.say("A point on the circle is its cosine and its sine.", Create(vec), FadeIn(dot), FadeIn(tag))
```

## 11. Recipe: a live number

No `DecimalNumber`. Redraw a `T` every frame from a `ValueTracker` with `always_redraw`. The redraw keeps running until you stop it, so call `clear_updaters()` before the number fades.

```python
self.chapter("A live number", "A number that counts while the voice talks.")
tracker = ValueTracker(0.0)
readout = always_redraw(lambda: T(f"{tracker.get_value():.2f}", 96, ACCENT, BOLD).move_to(UP * 0.8))
meter = always_redraw(lambda: Line(LEFT * 3, LEFT * 3 + RIGHT * 6 * tracker.get_value() / 100)
                      .set_stroke(ACCENT, 10).shift(DOWN * 1.0))
rail = Line(LEFT * 3, RIGHT * 3).set_stroke(LINE, 10).shift(DOWN * 1.0)
caption = T("percent done", 22, MUTED).move_to(DOWN * 1.8)
self.add(rail, readout, meter)
self.say("The count climbs from zero to a hundred.", FadeIn(caption), tracker.animate.set_value(100.0), run_time=3.0)
readout.clear_updaters()
meter.clear_updaters()
```
