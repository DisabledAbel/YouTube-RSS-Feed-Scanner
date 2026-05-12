# YouTube RSS Feed Scanner - Specification

## 1. Project Overview

**Project Name:** YouTube RSS Feed Scanner  
**Type:** Web Application (Single HTML file with embedded CSS/JS)  
**Core Functionality:** Users enter a YouTube channel URL/link, and the app returns the official RSS feed URL for that channel.  
**Target Users:** Content creators, podcasters, and power users who want to subscribe to YouTube channels via RSS readers.

---

## 2. UI/UX Specification

### Layout Structure

- **Single-page application** with centered content
- **Header:** App title and brief description
- **Main content area:** Input field + action button + results display
- **Footer:** Minimal credits

### Responsive Breakpoints

- Mobile: < 640px (full-width input, stacked button)
- Desktop: ≥ 640px (centered container, max-width 520px)

### Visual Design

**Color Palette:**
- Background: `#0f0f0f` (near-black)
- Card/Container: `#1a1a1a` (dark gray)
- Primary accent: `#ff0000` (YouTube red)
- Secondary accent: `#ffffff` (white text)
- Muted text: `#888888` (gray)
- Input background: `#252525`
- Input border: `#333333`
- Input focus border: `#ff0000`
- Success: `#00ff88` (bright green)
- Error: `#ff4444` (bright red)

**Typography:**
- Font family: `"IBM Plex Sans", sans-serif` (from Google Fonts)
- Title: 32px, font-weight 700
- Subtitle: 16px, font-weight 400, muted color
- Input text: 16px
- Button text: 16px, font-weight 600
- Result text: 14px, font-weight 500

**Spacing:**
- Container padding: 32px
- Element gap: 20px
- Input padding: 16px
- Button padding: 14px 28px

**Visual Effects:**
- Subtle box-shadow on container: `0 4px 24px rgba(0,0,0,0.5)`
- Input focus: red glow `0 0 0 2px rgba(255,0,0,0.3)`
- Button hover: slight scale (1.02) + brightness increase
- Results appear with fade-in animation (0.3s)

### Components

**Input Field:**
- Placeholder: "Paste YouTube channel URL here..."
- Full width
- Dark background with subtle border
- Focus state with red border glow

**Scan Button:**
- Full width on mobile, auto-width on desktop
- Red background, white text
- Hover: brightness 1.1, scale 1.02
- Active: scale 0.98
- Loading state: "Scanning..." with spinner

**Result Card:**
- Appears below input after successful scan
- Shows RSS feed URL in a copyable format
- Copy button with success feedback ("Copied!")
- Shows channel name if available

**Error Message:**
- Red-tinted background
- Displayed when invalid URL or parsing fails

---

## 3. Functionality Specification

### Core Features

1. **URL Input Parsing**
   - Accept various YouTube channel URL formats:
     - `https://www.youtube.com/@username`
     - `https://www.youtube.com/channel/UC...`
     - `https://www.youtube.com/c/channelname`
     - `https://www.youtube.com/user/username`
     - `https://www.youtube.com/@handle` (new format)
   - Extract channel ID from URL using multiple methods

2. **RSS Feed Generation**
   - Generate official YouTube RSS feed URL format:
     - `https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID`
   - Use YouTube's official RSS endpoint

3. **User Feedback**
   - Show loading state during processing
   - Display error for invalid inputs
   - Show success with RSS feed URL

4. **Copy to Clipboard**
   - One-click copy of RSS feed URL
   - Visual feedback on copy success

### User Interactions

1. User pastes YouTube channel URL into input field
2. User clicks "Get RSS Feed" button
3. App validates and parses the URL
4. App extracts channel ID
5. App generates RSS feed URL
6. App displays result with copy functionality

### Edge Cases

- Empty input → Show "Please enter a YouTube channel URL"
- Invalid URL → Show "Invalid YouTube channel URL"
- URL without valid channel → Show "Could not find valid channel ID"
- Network error → Show "Unable to process URL"

---

## 4. Acceptance Criteria

### Visual Checkpoints

- [ ] Dark theme with YouTube red accents renders correctly
- [ ] Input field has proper focus states
- [ ] Button has hover/active animations
- [ ] Result card fades in smoothly
- [ ] Copy button shows success feedback

### Functional Checkpoints

- [ ] `@username` format URL is parsed correctly
- [ ] `/channel/UC...` format URL is parsed correctly
- [ ] `/c/channelname` format URL is parsed correctly
- [ ] `/user/username` format URL is parsed correctly
- [ ] Generated RSS feed URL is valid and accessible
- [ ] Copy button copies URL to clipboard

### Test URLs

| Input | Expected Channel ID |
|-------|---------------------|
| `https://www.youtube.com/@GoogleDevelopers` | UC_x5go1Nu-17r9EBU11tHjQ |
| `https://www.youtube.com/channel/UCwX6rVkqpqXMPXj-J2-I2g` | UCwX6rVkqpqXMPXj-J2-I2g |
| `https://www.youtube.com/c/MarquesBrownlee` | UC-lHJZR3Gqxm24_Vj_AJ36A |