# AI Prompts — Homework 4

## Assignment goal

Build a shopping app with a React + Vite + TypeScript frontend and a Python FastAPI backend with a PydanticAI agent. Shoppers can browse products, create an account, chat about products and see matching items on the page, and get answers about pricing.

## How sections are written

There is one section for each problem. A section includes:

- The problem number and title
- The prompt typed for that problem
- Any follow-up prompts, only when they were needed

## Problems

## Problem 1: Vibe coder prompts

**Prompt:**

> Today we will focus on another project in my AI class. As with the other project we will go through different problems and create a final product. The goal for this product is to build a react +vite typescript front end and Python FASTAPI backend with a PydanticAI agent. Shoppers will be able to browse products, create and account, chat about products and see matching items on the page and get answers about pricing. I will give you the problems in order.

> Problem 1 titled Vibe coder prompts. create AI_prompts.md and update it as we work with what was typed

**Follow-up prompts:**

> Each section will represent 1 problem. Each session will include problem number and title. The prompt and any follow up prompt if needed.

## Problem 2: Analyze the database

**Prompt:**

> Problem 2: Analyze the database *(uploaded campus_customs.db)*

**Follow-up prompts:**

> are you able to read the file

> Start file output/harness.md. Write down each table and its fields and add one short line on why each field matters for the shop or the chatbot. We will keep growing this file in future sections

## Problem 3: Build the Campus Customs website

**Prompt:**

> Problem 3: Build the Campus Customs website. Scaffold a React +Vite + Typescript front end for Campus customs. Include a navigation bar that includes links to main pages. The categories include Home, Products, About Us, Log in and Create Account.  Home and About Us page will reflect the rich history of Yale University. Drawing on the rich tradition of the university and Campus Customs which was started in 1975. It is a family run business. There is alot of Yale pride showcasing the name in the classic yale blue and cream/white color

**Follow-up prompts:**

> On the products page, each product image from the catalogue should be shown (use the image paths in the database) provide the basic production information including the name, price and short description of product. Each product should open single item page, with a large image on the left side and full product text on the other. This text should give more details about product including description, price, sizes/stock when available. The product image will be an active link and by clicking on the card it takes the shopper to larger single item page.
>
> Add a chat interface in the bottom right of the site. it does not need to talk to agent yet but we will connect to backend later. You can start simple FASTAPT app in backend/main.py  just to serve products and images that we will use later to develop agent backend in next problem

## Problem 4: Create account and login

**Prompt:**

> Problem 4: Create account and login. Build a normal create account/login flow. the Create account should have first name and last name, email and password. you should have confirm password as well. The log in should include email and password. New accounts will go into the users table. We will make sure to store passwords securely so hackers cannot access them

**Follow-up prompts:**

> The seed database has a test user we can use while building. Email: test@campuscustoms.yale.edu; Password: password; Hash function: PBKDF2-HMAC-SHA256, 120,000 iterations (stored as pbkdf2_sha256$salt$hash)

> Still problem 4. After log in the password will be checked by the following rules. 1. never unhash the stored value. 2. Read the salt out of the stored string do not make a new one at login. 3. Hash the type password with that same salt then compare to the stored hash. Use a constant time compare. 4. signup and login must use the same has settings (same function, same salt handling, same iteration count). If they differ, even the right passwords will not match. Best method to check is to log in as the seeded test user and as a brand new account you just created in the app. Confirm that the use can log in and the brand new account created also works. Update output/harness.md with how auth works

## Problem 5: Pydantic AI agent backend

**Prompt:**

> Problem 5 : Pydantic AI agent backend. We will build the shop chatbot as a PydanticAI agent behind FASTAPI and plug it into the front end widget. Put the API app in backend/main.py. This file will run with Uvicorn. This agent will have 4 files including backend/prompts/prompt.md (system prompt), backend/agent.py (agent entry/wiring), backend/tools.py (tools the agent can call) and backend/models.py (Pydantic/PydanticAI structured types. In main.py expose a chat route so a message from the website returns a reply from the agent. You can use OPENAPI AI KEY from .env file in the root

**Follow-up prompts:**

> Put the Campus customs voice and safety basics into prompts/prompt.md. Start and update types in models.py for chat replies/product cards . In output/harness.md notw how the front end talks to FASATAPI and how the agent is loaded. Make sure the backend runs from the backend/ like uvicorn main:app --reload --port 8000

## Problem 6: Tools, product info and stock

**Prompt:**

> Problem 6: Toolls, product info and stock. Give agent tools that look up real information from campus_customs.db including product description, price and how many are in stock. Include by size if customer asks. The agent must use the database and not make up any information. If out of stock that should be clearly stated

**Follow-up prompts:**

> Continue to expand prompts/prompt.md with these tools . Also add/update: models.py In output/harness.md, list each tool and explain which model field you chose for lookup results and why

## Problem 7: Chat search that updates the page

**Prompt:**

> Problem 7: Chat search that updates the page. if asked about the type of order like what hoodies do you have, the agent should search catalogue and website should show those matching items as product cards. After the product cards are loaded as a dynamiclink make and use same single item page behavior built in problem 3. update prompts/prompts.md and output/harness.md on how to make sure how search results are handled

## Problem 8: Customer memory

**Prompt:**

> Problem 8: Customer memory. When a shopper is logged in, dave the chat history in the database in a table that can reload it when they return. The agent should document who is chatting including name and email. The agent then puts in tools the agent can call. Be sure to include enough page context so if person asks general question about an item on the page. like do you have this shirt in pink, the agent knows which item they mean. You can allow guests to chat but history should be retained for logged in users.
> Continue to update output/harness.md, including how user chat history is stored, what customer fields the agents sees and how page context is passed to answer general questions posed by user

## Problem 9: Usability improvements

**Prompt:**

> Problem 9: Usability improvements

> I want to verify the core shop works

**Follow-up prompts:**

> For back-end improvements you can make suggestions for customers when they type into a search box. You can also make the chat button pop up if customer is on page but not clicking on a product after a few seconds. Front end improvement, make the interface very modern. Use attractive  bold colors

> Write output/usability.med to list the before and as each build happens to improve usability. For each improvement state what was added and why it helps the campus customer shopper or business.

> let's confirm updates are working with stated improvements

> Additional improvements, is to keep search bar on top but the dropdown should disappear until the person is typing. Additional updates the first main page should have images of beautiful scenes taking into  account the beauty of Yale's campus and it should have a photos that have are moving in a reel of college age kids doing outdoor/indoor college activities.  The look of the website is very basic and not refined. The website should reflect the prestige of Yale and should be refined with beautiful graphics

> *(Answer to photo question: "Slots only, I'll add photos later")*

> Write output/design.md to document the changes in design and why it should help customers stick around and buy. In this case it should be attractive so that customers want to scroll and search

> You can add photos of gothic style beautiful buildings that are similar to yale's buildings if you can not use the licensed images

> Once you finish that let's test the site and document it in output/app_check.html and it should be a page you can double click to open. Include clear screenshots and short captions for 1. chat checking the inventory level of an item, 2. dynamic search results cards after category question. 3. one of the new usability features added. May html easy to grade. Heading for each check, screenshot and 1-2 sentences on what the screenshot proves. Put the screenshot image files in output/app_check_images and link them from app_check.html with relative paths for example app_check_images/invetory.png

## Problem 12: Audit trail, safety, finish harness

**Prompt:**

> Problem 12: audit trail, safety, finish harness. Keep an append only output//audit_trail.json of agent loop activity time including time, tool name, short args/results and stop reason. Do not wipe clean in between runs. The agent should be sure to be clear with password safety and create usability adjustments when instructed to improve user experience. Put these features in prompts/prompt.md

**Follow-up prompts:**

> finish output/harness.md that should detial how the system works. Model fields in models.py and why we chose them. Tools and abilities, safety rules, specs (loop limits, result caps, models and how to run front and back

## Publishing: live run and public GitHub

**Prompt:**

> lets run live site then we will push it to public Github. We will summary of this code in folder named Hw4

**Follow-up prompts:**

> Do not put real .env, campus_customs.db or product images in the Github repo

> Use .gitignore  and include .env.example with placeholders only

> Agent is four files backend/, prompts/prompt.md, agent.py, tools.py and models.py. The readme.md should explain how to run the front and backend after placing the data pack

> you can take the screenshots

> tell me how to connect chrome if needed

> ok my system does not allow the extension to be install. provide another way to complete the steps

> neither way is working

> let's move on

> can we check the live site

