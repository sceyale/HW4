# Design: Campus Customs (refined heritage redesign)

## Goal

The site should look as prestigious as Yale itself. It should be beautiful enough that shoppers **want to keep scrolling, start searching, and buy**.

The previous version used bold, bright colors but read as basic. This redesign keeps the strong Yale blue and adds the restraint, craft and detail you'd expect from a heritage brand.

## 1. Visual identity

| Element | Before | After | Why it helps customers stay and buy |
|---|---|---|---|
| **Palette** | Electric blue, sky, bright gold on white | **Yale navy** `#00356B` / deep navy `#001F45`, **ivory** `#FAF6EE`, **antique gold** `#C9A45C` hairlines, with coral and green only for stock status | Navy, ivory and gold signal heritage and quality, the way prestige brands present themselves. Shoppers trust the store more and feel the product is worth the price. |
| **Typography** | One heavy sans-serif | **Cormorant Garamond** serif for headings, product names and prices; **Inter** for body text and labels; wide-spaced small capitals for section labels | The serif headings echo carved stone and university printing. The clean sans-serif keeps details easy to read. The contrast gives a "crafted" feel that holds attention. |
| **Crest** | A text "CC" badge | An original **Campus Customs crest**: navy shield, gold double border, CC monogram, star and "1975". Used in the nav bar, hero and closing section. (An original design, not the Yale shield.) | A crest instantly says "established and authentic", builds brand recognition, and adds polish on every page. |
| **Details** | Thick borders, heavy shadows, bubbly corners | Thin gold lines, framed category tiles, diamond markers on the timeline, gold underlines that slide in on nav links, and softer, deeper shadows | Small, careful details are what make a site feel premium. Shoppers notice the quality even if they can't say why, and quality in the site suggests quality in the clothing. |

## 2. Home page, built to be scrolled

The Home page is now a **story told from top to bottom**. Each section ends with a reason to keep going.

| Section | What it is | Why it keeps shoppers scrolling and buying |
|---|---|---|
| **Cinematic hero** | A full-screen slideshow of campus scenes (Harkness Tower at dusk, Old Campus in autumn, Sterling Library, Beinecke in snow). Each slide slowly zooms (a "Ken Burns" effect) and fades into the next every 6.5 seconds. A navy veil keeps the text readable. The crest, an "Est. 1975 · New Haven" label and the headline **"Wear the Blue. *Carry the Tradition.*"** (the second line in gold italics) rise into view. There's a gold **Shop the collection** button and an outlined **Ask our shop assistant** button, plus a caption with indicator dots and a bouncing "Explore ↓" cue. | Movement and emotion in the first second make visitors stay. The story connects the clothing to campus memories, and the shopper's pride is the reason to buy. Two clear next steps (shop, or ask) mean no one is unsure what to do. The scroll cue invites them further down. |
| **Gold ribbon** | "Family-run since 1975 ✦ 100+ Yale styles ✦ Sizes XS–XXL ✦ Lux et Veritas" | Key reasons to trust and buy, readable in one glance. |
| **Shop by category** | Framed navy tiles in 3 shades. Each shows the live style count, the category in serif type, and the real starting price. On hover the frame turns gold and tightens, a glow grows, and the arrow slides. | Prices up front remove uncertainty. The hover effects make tiles feel tappable, and one click lands on a filtered Products page. |
| **The beauty of campus** | A photo mosaic: one large feature image plus 4 smaller ones (Cross Campus, a residential college courtyard, Phelps Gate, the Yale Bowl, Old Campus in snow), with serif italic captions. Images zoom gently on hover. | Beautiful imagery is what people scroll for. It builds the emotional pull that makes Yale apparel worth owning, right before the products. |
| **Bright college years (moving reel)** | A continuously scrolling reel of student-life photos on deep navy: crew at sunrise, library study, frisbee, The Game, a cappella, hockey, lab research, art studio, friends in Yale blue, Commencement. It pauses when the shopper hovers. | Motion holds the eye. Seeing students living the Yale experience, in Yale blue, is aspirational for prospective students, parents and alumni, who are the core buyers. |
| **Best of the season** | 4 real products from the catalogue (the best-stocked item in each category) as product cards, plus **View all products**. | Shoppers move from inspiration straight to buying while they're still engaged. |
| **Built on Bulldog history** | Milestones in large serif years (1701, 1875, 1889, 1975) on a ruled grid. | Heritage reinforces trust and pride, and the reason to buy from a 50-year family shop. |
| **Closing call to action** | Navy section with an inset gold frame, crest, *"Boola Boola."* and **Join the Campus Customs family**. | A warm final invitation to create an account. Accounts enable chat memory and repeat visits. |

### Photos

- **Slots:** every image lives in a named slot (`src/campusPhotos.ts`). Dropping a correctly named `.jpg` into `frontend/public/campus/` makes it appear automatically, fading in, with no code change. The checklist, sizes and licensing notes are in `frontend/public/campus/README.md`.
- **Until then:** licensed Yale photos couldn't be downloaded here, so the hero and gallery show **original illustrated Collegiate Gothic scenes** (`GothicScene.tsx`) in place of photos: towers with lit lancet windows, pinnacles, cloister arcades, a gate, elms, and dusk, autumn, stone, snow, green and night skies.
- **Reel placeholders:** these show refined colored panels with an elegant line icon for each activity (oar, book, frisbee, music, hockey, flask, palette, friends, mortarboard).
- **In development:** a small "Add photo: campus/…" label shows which file is missing. It's hidden in the production build.

## 3. Search: always there, never in the way

| Before | After | Why |
|---|---|---|
| A popular-searches dropdown opened as soon as the box was clicked, and there were extra search boxes on Home and Products | **One search bar, fixed at the top in the nav bar on every page.** The dropdown appears **only once the shopper starts typing**, and closes on Esc, a click outside, or a selection. | Search is always one glance away, so shoppers never have to hunt for it. The page stays clean until they act, which keeps the design calm and premium. |
| A bright white input | A subtle see-through pill on the navy bar with a gold icon. When focused it turns ivory with a gold glow. The dropdown has a gold top line, product thumbnails, prices and a gold **Ask** tag for the assistant. | Feels like part of the design rather than an add-on, so it gets used more. Thumbnails and prices let shoppers decide faster. |

## 4. The rest of the site, refined to match

- **Products:**
  - Navy page header with a gold rule.
  - Ivory product images.
  - Product names in serif type and categories in gold small capitals.
  - Gentle lift and zoom on hover.
  - Chat results in an ivory panel with a gold top line.
- **Single item page:**
  - Large serif name and price, with gold section labels.
  - Size boxes in serif type: navy outline = in stock, gold = only a few left, struck-through = sold out.
- **About:**
  - Gold-ringed "Est. 1975" seal.
  - Timeline with gold diamond markers and serif years.
- **Log in / Create account:** a white card with a gold top edge on navy, with refined small-caps labels.
- **Chat:**
  - Navy launcher with a gold border and an "Ask us" label.
  - Serif "Shop Assistant" title over a gold line, ivory conversation area, navy shopper bubbles.
  - The pop-up nudge restyled to match.
- **Accessibility and speed:**
  - Gold focus rings for keyboard users.
  - All motion switches off for people who turn on "reduce motion".
  - Layouts adapt to tablet and phone.
  - Photos load only when needed (lazy loading) and fade in.

## Why this should increase time on site and sales

1. **First impression:** a cinematic, prestigious hero earns the first 10 seconds, which is when most visitors decide whether to stay.
2. **A reason to scroll:** each section changes rhythm (photo, then tiles, then mosaic, then moving reel, then products, then history), so there's always something new below.
3. **Emotion before price:** campus beauty and student life make the clothing feel like belonging, not just merchandise.
4. **Many paths to products:** category tiles, favorites, the nav search and the AI assistant all lead to product pages within one or two clicks.
5. **Trust:** heritage styling, the 1975 crest, real prices and clear stock reduce hesitation at the moment of purchase.
