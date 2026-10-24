# Usability Improvements: Campus Customs (Problem 9)

Each improvement lists the **before**, **what was added**, **why it helps** the Campus Customs shopper or the business, and **how it was confirmed**.

## Baseline: verify the core shop works first

**Before:** each part had its own offline test, but nothing checked the whole shop working together.

**Added:** `backend/verify_shop.py`, a single end-to-end check against the running app. It covers:

- products and prices against the database
- all 102 images
- the website pages and the Vite connection to the API
- log in, create account and log out
- the chatbot (hoodie search, a sold-out size, "this shirt in pink?")
- saved history
- (new) search suggestions

**Why it helps:**

- **Shopper:** prices, stock and logins can be trusted.
- **Business:** a single command confirms the shop still works after any change, before customers see it.

**Confirmed:** offline suites pass (auth 10/10, tools and search 25/25, memory 18/18). Running `python verify_shop.py` checks the live app.

## 1. Search suggestions as you type (backend + search box)

| | |
|---|---|
| **Before** | No search box. Shoppers could only scroll the full 102-item grid or click category filters. A shopper who knew what they wanted ("bulldog", "hockey") had no quick way to find it. |
| **Added** | **Backend:** `GET /api/suggest?q=` returns matching categories (with style count and starting price), keyword ideas from product tags, up to 6 product matches (photo, price, sold-out flag) and a total count. It's a pure database lookup, with no AI call, so it's instant and free. It understands shopper words such as "Handsome Dan" → bulldog and "tee" → t-shirt. |
| | **Frontend** (`SearchBox.tsx`), in the nav bar on every page plus large versions on Home and Products: <br>- **Empty box:** shows popular searches. <br>- **While typing:** a dropdown with a "Search for …" row, categories, keywords and product thumbnails. <br>- **Keyboard:** up/down to move, Enter to choose, Esc to close. <br>- **Speed:** waits 150 ms after typing stops, and cancels outdated requests. <br>- **Ask our assistant about "…" (AI):** hands the question to the chatbot. |
| | **Results page:** Enter opens `/products?q=…`, ranked the same way as the chatbot's search, with "N results for 'q'", a Clear button, and a friendly empty state ("No products match… ask our shop assistant"). Search and category live in the URL, so results can be bookmarked or shared and the Back button works. |
| **Why it helps** | **Shopper:** finds a specific item in 2–3 keystrokes instead of scrolling 102 cards. Sees price and sold-out status before clicking. Is never stuck on "no results", because the assistant is one click away. |
| | **Business:** faster discovery means more product views and more sales. The search terms show what customers want. "Pink" and "shorts" get zero matches, which signals demand for products not yet stocked. |
| **Confirmed** | `test_tools.py` (7 new checks): <br>- An empty box gives popular searches. <br>- "hoo" gives the Hoodies category plus products. <br>- "fle" gives Fleeces & Jackets. <br>- "handsome dan" gives only bulldog items. <br>- "pink" gives 0 matches. <br>- Suggested prices match the catalogue. <br>- The results page returns every match. <br><br>`verify_shop.py` checks the live endpoint, including that it responds in under 500 ms. |

## 2. Chat pop-up when a shopper lingers

| | |
|---|---|
| **Before** | The chat was a small "Chat" circle. Shoppers who didn't notice it, or didn't know what to ask, browsed alone and often left. |
| **Added** | A nudge in `ChatWidget.tsx`. If a shopper stays on Home, Products or About for **8 seconds** without opening a product, using search or opening chat, the chat button **bounces** and a speech bubble appears. |
| | **The bubble:** "Looking for something Yale?" with 2 one-tap questions. On the Products page it matches the filter, e.g. "Need help with Hoodies?" with "What hoodies are in stock in M?" and "Cheapest hoodies?". |
| | **Rules:** <br>- Shown at most once per visit (`sessionStorage`). <br>- Never on login or signup pages, or on an item page (they already found something). <br>- Never after the shopper has chatted. <br>- Cancelled the moment they click a product card or the search box. <br>- Dismissable with ×. |
| | **Launcher:** the button is now a larger pill with a chat icon and "Ask us" (icon only on phones). |
| **Why it helps** | **Shopper:** help appears exactly when they seem undecided, with ready-made questions, so they don't have to think of what to type. It stays out of the way once they're engaged. |
| | **Business:** turns hesitant browsers into conversations, and conversations show product cards, which means more chances to sell. The once-per-visit limit avoids annoying customers. |
| **Confirmed** | The code builds cleanly. To check by hand: <br>1. Open Home and wait 8 seconds: the button bounces and the bubble appears. <br>2. Reload and click a product within 8 seconds: no bubble. <br>3. Tap a suggested question: the chat opens and sends it. <br>4. Open a new tab in the same visit: no second bubble. |

## 3. Modern interface with bold colors

| | |
|---|---|
| **Before** | Classic and quiet: flat Yale blue header, serif headings, cream panels, thin borders. Pleasant, but dated and low-contrast for calls to action. |
| **Added** | A full redesign in `index.css`, Home and NavBar. The class names are unchanged, so all pages pick it up. |
| | **Bold palette:** Yale blue core, plus **electric blue** `#1F6BFF`, **sky** `#45C4FF`, **gold** `#FFC72C`, **coral** for sold out and **mint** for in stock. Layered gradient hero. |
| | **Modern type:** heavy 800–900 sans-serif headings with tight spacing. The word "YALE" has a gold-to-sky gradient. |
| | **Glass nav bar:** a blurred, see-through header with a "CC" brand mark and the search box built in. |
| | **Home page:** <br>- A large hero with a big search box, a gold "Shop all products" button and a glass "Ask the shop assistant" button. <br>- A slanted gold scrolling banner: "BOOLA BOOLA ✦ GO BULLDOGS ✦ EST. 1975". <br>- **Category tiles** in bold colors with live style counts and starting prices, each linking to the filtered Products page. |
| | **Cards:** rounded corners (24 px), soft shadows. They lift on hover and the image zooms slightly. |
| | **Item page:** <br>- The price sits in a gold pill. <br>- Size boxes are color-coded: green = in stock, gold = only a few left, coral with strikethrough = sold out. |
| | **Chat:** gradient header, electric-blue user bubbles, and a gradient-bordered "From your chat" strip. |
| | **Accessibility:** clear focus rings. Animations switch off for shoppers who turn on reduced motion. Works on phones. |
| **Why it helps** | **Shopper:** easier to scan. Bold color shows what to tap next (gold = buy or browse, electric blue = the assistant). Stock status is readable at a glance from color alone. Feels like a current, trustworthy store. |
| | **Business:** a modern look builds trust and keeps the brand fresh for students while honoring the 1975 heritage. Category tiles and bigger calls to action push shoppers further into the shop. |
| **Confirmed** | The CSS bundles cleanly. A scan confirmed every class used in the components has a style. `output/design_preview.html` renders the new Home hero, the search dropdown, the category tiles, the "From your chat" product grid with real photos, and the chat nudge using the real CSS. |

## 4. Small fixes made along the way

| Before | After | Why it helps |
|---|---|---|
| The category filter was lost on reload or when the link was shared | The filter and search are kept in the URL (`?category=` and `?q=`) | Back button, bookmarks and shared links all work |
| The Home page had no way into a category | Category tiles link straight to the filtered Products page | One click from Home to the right products |
| A search with no results showed an empty grid | Friendly empty-state message plus a pointer to the assistant | The shopper is never at a dead end |
| The chat launcher said only "Chat" | Icon plus "Ask us", and it bounces when the nudge appears | More noticeable and inviting, without being pushy |

## 5. Search bar always on top; dropdown only while typing

| | |
|---|---|
| **Before** | Clicking the search box immediately opened a "Popular searches" panel, and there were extra search boxes in the Home hero and the Products header. |
| **Added** | **One search bar, fixed at the top** (nav bar, every page). The suggestions dropdown stays hidden until the shopper **types**, and fetches only then. It closes on Esc, a click outside, or a selection. The extra boxes were removed. |
| **Why it helps** | **Shopper:** search is always in the same place, and the page isn't covered by a panel they didn't ask for. <br>**Business:** a calmer, more premium look, with search still one keystroke away. |
| **Confirmed** | The code builds cleanly. The panel only renders when the box has text in it. To check by hand: click the box (nothing opens), type "h" (the dropdown appears), press Esc (it closes). |

## 6. Refined, prestigious design (see `output/design.md`)

| | |
|---|---|
| **Before** | Bold electric colors. Functional, but basic and not refined. |
| **Added** | **Look:** Yale navy, ivory and antique gold. Serif display type (Cormorant Garamond). An original Campus Customs crest. Thin gold lines throughout. <br>**Home page:** a cinematic full-screen hero slideshow of campus scenes, a "beauty of campus" photo mosaic, a continuously moving student-life reel, "Best of the season" products and a heritage timeline. <br>**Photos:** named slots that switch to real photos when files are added to `frontend/public/campus/`. Until then, original illustrated Gothic scenes and activity icons fill them. |
| **Why it helps** | Prestige styling builds trust and makes the clothing feel worth owning. Movement and imagery give shoppers a reason to keep scrolling, and every section leads to products, search or the assistant. |
| **Confirmed** | The code builds cleanly, and every class the components use has a style. Screenshots are in `output/app_check.html`. |

## How to confirm everything

```
cd backend  && uvicorn main:app --reload --port 8000      # terminal 1
cd frontend && npm run dev                                 # terminal 2
cd backend  && python verify_shop.py                       # terminal 3 (automated checks)
```

Then try these by hand at http://localhost:5173:

1. Type "hoo" in the top search box: the dropdown shows Hoodies, keywords and product photos. Press Enter for the results page.
2. Type "pink" and choose "Ask our assistant about 'pink'": the chat opens and answers.
3. Stay on Home for 8 seconds: the chat button bounces and the help bubble appears.
4. Click a category tile, then a product: you see color-coded sizes and the gold price.
5. Resize to phone width: the menu collapses, and the chat and search still work.
