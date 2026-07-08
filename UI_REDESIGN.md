# NyayaSetu UI/UX Transformation Specification

## ROLE

You are an expert Senior Product Designer, UI/UX Architect, Frontend Engineer, and Design Systems Engineer with over 15 years of experience designing world-class AI products.

You have previously designed products with the level of quality seen in:

- Perplexity AI
- Claude AI
- Cursor
- Linear
- Notion AI
- Apple VisionOS
- Arc Browser
- Raycast
- Vercel

Your responsibility is to transform the existing frontend into a premium AI Legal Intelligence Platform while preserving every existing backend functionality.

You are expected to make production-quality design decisions, not simply generate UI components.

---

# PROJECT CONTEXT

Project Name:

NyayaSetu

Tagline:

Your AI Legal Rights Navigator

NyayaSetu is an AI-powered legal assistant built specifically for Indian citizens.

Unlike traditional chatbots, NyayaSetu uses Retrieval-Augmented Generation (RAG) to retrieve relevant legal provisions from real Indian legal documents stored in ChromaDB before generating responses using Groq Llama 3.1.

The interface should communicate trust, intelligence, professionalism, and authority.

The user should immediately understand that this is an AI-powered Legal Intelligence Platform—not a generic chatbot.

---

# CURRENT STACK

Backend

- FastAPI
- Python
- LangChain
- ChromaDB
- SentenceTransformers
- Groq API

Frontend

- HTML
- CSS
- Vanilla JavaScript

Do NOT migrate the project to React, Vue, Angular, NextJS or any other frontend framework.

Remain lightweight.

---

# PRIMARY OBJECTIVE

Completely redesign the frontend experience while preserving all backend functionality.

Do NOT modify

- FastAPI
- API routes
- Python code
- ChromaDB
- RAG pipeline
- Embedding pipeline
- Prompt generation
- Groq integration

Only improve

- HTML
- CSS
- JavaScript
- Layout
- Components
- Animations
- User Experience
- Responsiveness

---

# DESIGN PHILOSOPHY

The application should feel like a premium AI SaaS platform.

It should combine the elegance of Claude, the clarity of Perplexity, the refinement of Apple VisionOS, and the polish of Linear while maintaining its own unique legal identity.

Avoid making it look like ChatGPT.

The design language should emphasize:

- Trust
- Accuracy
- Professionalism
- Minimalism
- Readability
- Modern AI
- Premium Experience

---

# VISUAL STYLE

Use modern glassmorphism.

Requirements:

- Frosted glass
- Large backdrop blur
- Layered transparency
- Floating panels
- Ambient lighting
- Elegant shadows
- Rounded corners
- Smooth gradients
- Soft glowing borders
- Depth throughout the interface

The UI should never feel flat.

---

# COLOR PALETTE

Primary

Royal Purple

Deep Indigo

Secondary

Dark Navy

Accent

Gold

Emerald Green

Background

Dark animated gradient

Text

Soft White

Muted Gray

Maintain excellent contrast and accessibility.

---

# BACKGROUND

Replace the static background with an animated premium background.

Include

- slow moving gradients
- blurred glowing orbs
- ambient lighting
- subtle particle movement
- soft depth

Animation should be smooth and never distracting.

---

# LAYOUT

Completely redesign the layout.

Desktop Layout

------------------------------------------------

Sidebar

Main Conversation

Sources Panel

------------------------------------------------

Use the entire screen.

Avoid large unused empty spaces.

Spacing should feel intentional.

---

# SIDEBAR

Include

- NyayaSetu Logo
- New Chat
- Conversation History
- Search Chats
- Pinned Chats
- Categories
- Consumer
- Property
- RTI
- Traffic
- Criminal
- Family
- Cyber Crime
- Employment
- Constitution
- Bookmarks
- Settings
- About

Sidebar should collapse elegantly.

---

# LANDING EXPERIENCE

Before the first question is asked, show a premium landing screen.

Include

Large Logo

NyayaSetu

Subtitle

Large search box

Suggested prompts

Popular legal categories

Recent searches

Quick actions

Examples

Can my landlord evict me?

How do I file an RTI?

Consumer complaint process

Cyber crime reporting

Traffic challan rules

Employment rights

Property registration

Women rights

GST

This should resemble a modern AI search experience.

---

# SEARCH BAR

Create a floating premium search experience.

Include

- rounded corners
- glassmorphism
- send button
- voice input
- attachment
- optional image upload
- auto-resizing textarea
- beautiful focus animations

---

# CHAT EXPERIENCE

Modern conversational interface.

Support

- conversation history
- rename chat
- delete chat
- pin chat
- search conversations
- smooth scrolling
- typing animation
- streaming responses
- beautiful transitions

---

# RAG VISUALIZATION

Since this application uses Retrieval-Augmented Generation, visually expose that process.

Instead of showing a loading spinner, animate the pipeline.

Display stages such as

Searching legal database...

Finding relevant legal sections...

Ranking retrieved documents...

Preparing legal context...

Generating AI response...

This should reassure users that the answer is backed by retrieved legal documents.

---

# RESPONSE DESIGN

Never render responses as one long block of text.

Split every response into beautiful glass cards.

Cards should include

Quick Summary

Relevant Legal Provisions

Legal Interpretation

Actionable Steps

Things to Remember

Exceptions

Sources

Disclaimer

Each card should have

- icon
- title
- spacing
- subtle animation
- elegant typography
- glass effect

---

# SOURCE PANEL

Create a dedicated panel for legal references.

Display

Retrieved Acts

Sections

Articles

Page Numbers

Confidence Score

Open PDF

Expand Source

Copy Citation

Users should immediately understand where every answer originated.

---

# CONFIDENCE INDICATOR

Display an answer confidence meter based on retrieval quality.

Example

Answer Confidence

94%

Based on retrieved legal documents.

Represent this visually with a modern progress indicator.

---

# MICRO INTERACTIONS

Every interaction should feel polished.

Animate

Buttons

Cards

Sidebar

Search

Accordions

Hover

Focus

Scrolling

Loading

Expanding citations

Nothing should abruptly appear.

---

# TYPOGRAPHY

Use premium typography.

Preferred fonts

- Inter
- Manrope
- General Sans
- Satoshi

Large headings.

Readable legal text.

Excellent spacing.

---

# ICONS

Use Lucide icons throughout the application.

Maintain consistency.

Avoid excessive emoji usage.

---

# RESPONSIVENESS

Desktop-first.

Fully responsive.

Tablet optimized.

Mobile friendly.

Sidebar collapses.

Cards stack gracefully.

No horizontal scrolling.

---

# ACCESSIBILITY

Maintain

- keyboard navigation
- ARIA labels
- readable font sizes
- accessible contrast
- visible focus states

---

# PERFORMANCE

Maintain excellent performance.

Avoid unnecessary JavaScript.

Use GPU-accelerated CSS animations.

Lazy load where appropriate.

Keep the application lightweight.

---

# CODE QUALITY

Refactor the frontend where necessary.

Improve

- folder organization
- reusable components
- CSS architecture
- JavaScript organization

Remove duplicated CSS.

Improve maintainability.

---

# FINAL GOAL

When someone opens NyayaSetu, they should immediately feel they are using an enterprise-grade AI Legal Intelligence Platform built by a top AI company.

The interface should be premium enough to showcase on:

- Awwwards
- Behance
- Dribbble
- Product Hunt

without sacrificing usability or performance.

Do not stop after cosmetic improvements.

Critically evaluate every screen, every interaction, every layout decision, and every component.

If any part of the interface can be made more intuitive, more beautiful, more professional, or more trustworthy while preserving functionality, implement those improvements.

Work iteratively until the UI reaches production-level quality.

Do not ask for confirmation after every change. Analyze the existing frontend, identify weaknesses, redesign them thoughtfully, preserve all backend integrations, and deliver a polished, cohesive, responsive, and visually outstanding application.


IMPORTANT:

Before making changes, thoroughly inspect the entire project structure and understand how the current frontend interacts with the FastAPI backend.

Preserve all existing functionality.

Do not introduce regressions.

After each major change, verify that:
- API communication still works.
- All existing features remain functional.
- No JavaScript errors are introduced.
- The application remains responsive.
- The design system is consistent across all pages.

Prioritize quality over speed. Think like a senior engineer performing a production redesign, not a code generator making superficial changes.