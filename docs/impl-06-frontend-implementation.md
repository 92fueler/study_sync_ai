# Implementation: Frontend (Next.js)

> **Document**: impl-06-frontend-implementation.md  
> **Purpose**: Step-by-step frontend implementation plan  
> **Tech Stack**: Next.js 15, React 19, TypeScript, Tailwind CSS, Lucide React

---

## Overview

Building a pixel-perfect Next.js frontend based on 4 UI screenshots with consistent navigation and design system.

**Pages to Build**:
1. Dashboard (Home / Command Center)
2. Learning DNA (Personalization)
3. Learning Plan (Roadmap)
4. Knowledge Bank (Ingestion Engine)

---

## Phase 1: Project Setup ✅

**Status**: COMPLETED

- ✅ Removed old frontend folder
- ✅ Initialized Next.js with TypeScript
- ✅ Installed Tailwind CSS
- ✅ Installed Lucide React for icons

**Next Steps**:
- Configure Tailwind with custom colors
- Add Google Fonts (Serif + Sans-serif)
- Set up project structure

---

## Phase 2: Configuration & Design System

### 2.1 Tailwind Configuration

**File**: `tailwind.config.js`

Add custom colors from design spec:

```js
module.exports = {
  theme: {
    extend: {
      colors: {
        'trust-blue': '#2563EB',
        'pale-amber': '#FEF3C7',
        'success-green': '#10B981',
        'warning-orange': '#F59E0B',
      },
      fontFamily: {
        'serif': ['Playfair Display', 'serif'],
        'sans': ['Inter', 'sans-serif'],
      },
    },
  },
}
```

### 2.2 Google Fonts Setup

**File**: `app/layout.tsx`

Import fonts:
```tsx
import { Inter, Playfair_Display } from 'next/font/google'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const playfair = Playfair_Display({ subsets: ['latin'], variable: '--font-playfair' })
```

### 2.3 Project Structure

```
frontend/
├── app/
│   ├── layout.tsx           # Root layout with fonts
│   ├── page.tsx             # Dashboard (/)
│   ├── dna/
│   │   └── page.tsx         # Learning DNA
│   ├── plan/
│   │   └── page.tsx         # Learning Plan
│   └── bank/
│       └── page.tsx         # Knowledge Bank
├── components/
│   ├── shared/
│   │   ├── top-nav.tsx      # Navigation bar
│   │   ├── progress-ring.tsx
│   │   ├── status-badge.tsx
│   │   ├── card.tsx
│   │   ├── button.tsx
│   │   └── file-upload-zone.tsx
│   ├── dashboard/
│   │   ├── hero-input-zone.tsx
│   │   ├── active-paths-grid.tsx
│   │   ├── quote-card.tsx
│   │   └── recent-objects-carousel.tsx
│   ├── dna/
│   │   ├── format-preferences.tsx
│   │   ├── cognitive-tone.tsx
│   │   ├── style-matcher.tsx
│   │   └── dna-preview.tsx
│   ├── plan/
│   │   ├── proposed-plans.tsx
│   │   ├── plan-card.tsx
│   │   └── existing-plans.tsx
│   └── bank/
│       ├── batch-upload-zone.tsx
│       ├── live-status.tsx
│       └── topic-clusters.tsx
├── lib/
│   └── api.ts               # API client
└── public/
    └── logo.svg
```

---

## Phase 3: Shared Components

### 3.1 TopNav Component

**File**: `components/shared/top-nav.tsx`

**Requirements** (from screenshots):
- Fixed position at top
- White background with bottom border
- Height: 64px
- Left: Logo + optional search
- Center: 4 nav links (Dashboard, My DNA, Learning Plan, Knowledge Bank)
- Right: Search icon, bell icon, settings icon (optional), user avatar

**Props**:
```tsx
interface TopNavProps {
  showSearch?: boolean;
  showSettings?: boolean;
  userName?: string;
  userAvatar?: string;
}
```

**Implementation Notes**:
- Active link should have blue text color
- Use Lucide React icons: Search, Bell, Settings
- User avatar: circular with name next to it

### 3.2 ProgressRing Component

**File**: `components/shared/progress-ring.tsx`

**Requirements**:
- Circular SVG progress indicator
- Percentage in center (large serif font)
- Color-coded by status (blue/green/gray)
- Size variants: small (48px), medium (80px), large (120px)

**Props**:
```tsx
interface ProgressRingProps {
  percentage: number;
  size?: 'small' | 'medium' | 'large';
  color?: 'blue' | 'green' | 'gray' | 'orange' | 'purple';
  showLabel?: boolean;
}
```

### 3.3 StatusBadge Component

**File**: `components/shared/status-badge.tsx`

**Requirements**:
- Small pill shape
- Color-coded backgrounds
- Uppercase text
- Variants: processing, complete, ready, draft, paused, active

**Props**:
```tsx
interface StatusBadgeProps {
  status: 'processing' | 'complete' | 'ready' | 'draft' | 'paused' | 'active' | 'ingesting';
  text?: string;
}
```

### 3.4 Card Component

**File**: `components/shared/card.tsx`

**Requirements**:
- White background
- Rounded corners (8px)
- Subtle shadow
- Hover: slight lift effect
- Optional: dashed border, colored left border

**Props**:
```tsx
interface CardProps {
  children: React.ReactNode;
  variant?: 'default' | 'dashed' | 'bordered';
  borderColor?: string;
  className?: string;
}
```

### 3.5 Button Component

**File**: `components/shared/button.tsx`

**Requirements**:
- Primary: Trust blue background, white text
- Secondary: White background, gray border
- Icon support (Lucide React)

**Props**:
```tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary';
  icon?: React.ReactNode;
  children: React.ReactNode;
  onClick?: () => void;
}
```

### 3.6 FileUploadZone Component

**File**: `components/shared/file-upload-zone.tsx`

**Requirements**:
- Dashed border
- Drag & drop support
- Upload icon
- File type restrictions
- Size limit display

**Props**:
```tsx
interface FileUploadZoneProps {
  onUpload: (files: File[]) => void;
  acceptedTypes?: string[];
  maxSize?: number;
  title?: string;
  subtitle?: string;
}
```

---

## Phase 4: Page 1 - Knowledge Bank

**Route**: `/bank`  
**File**: `app/bank/page.tsx`

### Components to Build

#### 4.1 Batch Upload Zone
- Large dashed border card
- Cloud upload icon
- "Select Files" button
- "OR DRAG FILES HERE" text
- Supported formats text

#### 4.2 Live Status Section
- Heading with "View All Activity" link
- 3 horizontal status cards
- Each card shows: icon, title, status badge, description, timestamp

#### 4.3 Topic Clusters Grid
- Filter tabs: All, Recently Added, Favorites
- View toggle: List/Grid
- 4 cluster cards in grid
- Each card: thumbnail, type badge, title, description, tags, metadata

#### 4.4 Add Topic Manually Card
- Plus icon
- Title and description
- Dashed border

### API Integration
- `POST /api/v1/upload` - File upload
- `GET /api/v1/content?user_id={id}` - List content

---

## Phase 5: Page 2 - Learning DNA

**Route**: `/dna`  
**File**: `app/dna/page.tsx`

### Layout
- Two-column: 70% left, 30% right

### Left Panel Components

#### 5.1 Format Preferences
- Label with "Select all that apply"
- 3 multi-select cards
- Each card: icon, title, description, checkmark when selected
- Blue border when selected

#### 5.2 Cognitive Tone
- 4 pill buttons: Academic, Socratic, ELI5, Bulleted
- Selected state: blue background
- Explanation text below

#### 5.3 Style Matcher
- Dashed border upload zone
- Document icon
- "Click to upload or drag and drop" text
- "Browse Files" button

### Right Panel Components

#### 5.4 DNA Preview Card
- Circular progress ring (75%)
- Profile label: "Visual & Socratic"
- Description text
- Tags: #VisualLearner, #TimeCompressed, #SocraticMethod
- "Update Learning DNA" button (full width, blue)
- Last updated timestamp

#### 5.5 Need Guidance Card
- Dark background
- Title and description
- "Start Assessment →" button

### API Integration
- `POST /api/v1/profile` - Save preferences
- `GET /api/v1/profile/{user_id}` - Load DNA

---

## Phase 6: Page 3 - Learning Plan

**Route**: `/plan`  
**File**: `app/plan/page.tsx`

### Components to Build

#### 6.1 Page Header
- Title: "Your Learning Roadmap" (serif)
- Subtitle
- Dropdown: "Fall Term 2024"
- "View History" button

#### 6.2 Newly Proposed Plans Section
- Heading with "2 New" badge
- Two cards side-by-side:

**Draft Card**:
- Dashed border, pale amber background
- "DRAFT PROPOSAL" badge
- Title
- Warning icon + conflict message
- "Review Details" + "Confirm & Sync" buttons

**Ready Card**:
- Solid border, green accent
- "READY TO SYNC" badge
- Title
- Checkmark + success message
- "Review Details" + "Confirm & Sync" buttons

#### 6.3 Existing Learning Plans Section
- Filter tabs: Active (2), Paused (1), Completed
- Grid of plan cards

**Plan Card**:
- Left border (4px, color-coded)
- Status badge
- Title + difficulty
- Circular progress ring
- Next session time
- Three-dot menu

### API Integration
- `GET /api/v1/queue?user_id={id}` - Get proposed plans
- `POST /api/v1/calendar/sync` - Confirm & sync

---

## Phase 7: Page 4 - Dashboard

**Route**: `/`  
**File**: `app/page.tsx`

### Components to Build

#### 7.1 Hero Input Zone
- Large serif heading: "Structure your chaos into clarity"
- Tab buttons: Raw Notes, URL Input, Upload PDF
- Large textarea
- Bottom icons: Attach, Voice
- "Generate Structure" button (blue, prominent)

#### 7.2 Active Learning Paths Grid
- Heading with "View All" link
- 3 cards in grid
- Each card:
  - Category badge (SCIENCE, HUMANITIES, TECH)
  - Title + subtitle
  - Large serif percentage (78%, 34%, 12%)
  - Progress bar (color-coded)
  - Time remaining

#### 7.3 Philosophical Quote Card
- Italic serif text
- Attribution: "— SOCRATES"
- Light background

#### 7.4 Recent Smart Objects Carousel
- Horizontal scroll
- Navigation arrows
- Cards: icon, title, timestamp

### API Integration
- `GET /api/v1/queue?user_id={id}` - Active paths
- `GET /api/v1/content?user_id={id}&sort=rank` - Recent objects

---

## Phase 8: API Client Setup

**File**: `lib/api.ts`

Create API client with:
- Base URL configuration
- Request/response interceptors
- Error handling
- TypeScript types

```tsx
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api = {
  upload: (files: File[]) => { /* ... */ },
  getContent: (userId: string) => { /* ... */ },
  getProfile: (userId: string) => { /* ... */ },
  saveProfile: (data: ProfileData) => { /* ... */ },
  getQueue: (userId: string) => { /* ... */ },
  syncCalendar: (planId: string) => { /* ... */ },
};
```

---

## Phase 9: Testing & Polish

### 9.1 Visual Testing
- [ ] Compare each page to screenshots pixel-by-pixel
- [ ] Verify colors match exactly
- [ ] Check font sizes and weights
- [ ] Verify spacing and alignment

### 9.2 Responsive Design
- [ ] Test on desktop (1920px, 1440px, 1280px)
- [ ] Test on tablet (768px)
- [ ] Test on mobile (375px)

### 9.3 Interactions
- [ ] Hover states on buttons and cards
- [ ] Click interactions
- [ ] File upload drag & drop
- [ ] Form submissions

### 9.4 Integration
- [ ] Connect to backend API
- [ ] Test data loading
- [ ] Test error states
- [ ] Test loading states

---

## Implementation Order

1. ✅ **Setup** - Next.js, Tailwind, Lucide React
2. **Configuration** - Tailwind colors, Google Fonts
3. **Shared Components** - TopNav, ProgressRing, StatusBadge, Card, Button, FileUploadZone
4. **Knowledge Bank Page** - Highest priority (core ingestion)
5. **Learning DNA Page** - Preference engine
6. **Learning Plan Page** - Calendar integration
7. **Dashboard Page** - Command center
8. **API Integration** - Connect to backend
9. **Testing & Polish** - Pixel-perfect matching

---

## Key Design Principles

1. **Pixel-Perfect Matching**: Every element must match the screenshots exactly
2. **No Placeholders**: Write full code, no comments like "// Add more items"
3. **Exact Colors**: Use hex values from design spec
4. **Exact Text**: Use text from screenshots verbatim
5. **Repeat Elements**: If screenshot shows 15 items, code must have 15 items
6. **Lucide Icons**: Use lucide-react for all icons
7. **Google Fonts**: Playfair Display (serif) + Inter (sans-serif)
8. **Tailwind Only**: No custom CSS files

---

## Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_USER_ID=test-user-123
```

---

## Success Criteria

- [ ] All 4 pages match screenshots exactly
- [ ] Consistent navigation across all pages
- [ ] All colors match design spec
- [ ] All fonts match (serif for emphasis, sans for body)
- [ ] All interactions work (hover, click, drag & drop)
- [ ] API integration functional
- [ ] No TypeScript errors
- [ ] No console warnings
- [ ] Responsive on all screen sizes
- [ ] Accessible (keyboard navigation, screen readers)

---

## Next Steps

1. Configure Tailwind with custom colors and fonts
2. Build shared components (TopNav, ProgressRing, etc.)
3. Build Knowledge Bank page (first priority)
4. Build remaining pages in order
5. Integrate with backend API
6. Test and polish

---

## Estimated Timeline

- **Phase 2 (Config)**: 30 minutes
- **Phase 3 (Shared Components)**: 2 hours
- **Phase 4 (Knowledge Bank)**: 2 hours
- **Phase 5 (Learning DNA)**: 2 hours
- **Phase 6 (Learning Plan)**: 2 hours
- **Phase 7 (Dashboard)**: 2 hours
- **Phase 8 (API Integration)**: 1 hour
- **Phase 9 (Testing & Polish)**: 2 hours

**Total**: ~13-14 hours
