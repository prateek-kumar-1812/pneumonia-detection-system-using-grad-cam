# PneumoVision AI - Quick Reference Guide

## 🚀 Start Here

### Is the app running?
✅ **YES** - Dev server running on http://localhost:8081/x-ray-vision-clarity/

### What does it do?
Analyzes chest X-ray images using AI to detect pneumonia and shows where the model's attention focused using Grad-CAM visualization.

### Can I test it now?
✅ **YES** - Open the preview and upload any image (or test with the demo mode that's currently active)

---

## 📋 File Guide

### Must-Know Files

| File | Purpose | Edit When |
|------|---------|-----------|
| `src/App.tsx` | Router & State | Adding routes or global state |
| `src/pages/Index.tsx` | Main Page Logic | Changing app flow or state management |
| `src/components/FileUpload.tsx` | Upload Component | Modifying upload behavior or validation |
| `src/components/ResultsDisplay.tsx` | Results Display | Changing result visualization |
| `src/lib/api.ts` | API Integration | Connecting real backend |
| `src/index.css` | Global Styles | Changing colors, fonts, animations |
| `tailwind.config.ts` | Tailwind Config | Customizing theme |

### Component Files
```
components/
├── Header.tsx              → Top navigation
├── HeroSection.tsx         → Hero banner
├── FileUpload.tsx          → Image upload (important)
├── LoadingAnalysis.tsx     → Loading animation
├── ResultsDisplay.tsx      → Results display (important)
├── Footer.tsx              → Footer
└── ui/                     → shadcn/ui components (don't edit)
```

---

## 🎯 Common Tasks

### Change Colors
**File:** `src/index.css`

Find the `:root` CSS variables section and modify:
```css
--primary: 210 65% 25%;        /* Main blue */
--accent: 175 60% 40%;         /* Teal accent */
--destructive: 0 72% 51%;      /* Red for alerts */
--success: 152 60% 40%;        /* Green for success */
```

### Change Fonts
**File:** `src/index.css` (import section)

Currently using:
- **Headings:** Plus Jakarta Sans
- **Body:** Inter

Change the Google Fonts import at the top.

### Connect Flask Backend
**File:** `src/lib/api.ts`

1. Set environment variable: `VITE_API_URL=http://localhost:5000`
2. Change the demo function to the real one in `Index.tsx`:
   ```typescript
   // From:
   const prediction = await predictPneumoniaDemo(file);
   // To:
   const prediction = await predictPneumonia(file);
   ```

### Modify Upload Validation
**File:** `src/components/FileUpload.tsx`

Find `validateFile()` function - modify:
- Accepted file types: `validTypes` array
- File size limit: `file.size > 10 * 1024 * 1024` (currently 10MB)

### Change Result Display
**File:** `src/components/ResultsDisplay.tsx`

Modify the grid layout, card styling, or add new sections.

---

## 🔍 Component Deep Dives

### FileUpload Component
**What it does:** Handles X-ray image upload with drag-drop  
**Key props:**
- `onFileSelect(file)` - Called when file is selected
- `isLoading` - Shows loading state

**States:**
- No file selected → Shows drop zone
- File selected → Shows preview with analyze button
- Error → Shows error message

### ResultsDisplay Component
**What it does:** Shows prediction results and visualizations  
**Props:**
- `result` - Prediction data (label, probability, gradcam, overlay)
- `originalImage` - Original X-ray image
- `onReset()` - Called to analyze another image

**Displays:**
1. Prediction card (with confidence bar)
2. Three-image grid (original, gradcam, overlay)
3. Explainability section
4. Medical disclaimer

### LoadingAnalysis Component
**What it does:** Shows animated loading state during AI processing  
**Features:**
- Spinning circle animation
- Progress steps with staggered timing
- "Analyzing..." message

---

## 🛠️ Development Workflow

### I want to modify the UI
1. Edit component files in `src/components/`
2. Save - automatic reload in browser
3. Preview changes at http://localhost:8081/x-ray-vision-clarity/

### I want to add a new feature
1. Create component in `src/components/`
2. Import in `src/pages/Index.tsx`
3. Add to JSX
4. Test in preview

### I want to add a new color
1. Edit `src/index.css` - add to `:root` or `.dark`
2. Use in components: `className="bg-[your-css-var]"`
3. Or add Tailwind class in `tailwind.config.ts`

### I want to test without backend
✅ Already working! Demo mode is active - just upload an image and it simulates results.

---

## 📱 Responsive Design

### Tailwind Breakpoints
- **Default:** Mobile (0-640px)
- **md:** `md:` prefix - tablets (768px+)
- **lg:** `lg:` prefix - desktops (1024px+)

Example:
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
  {/* 1 column mobile, 2 tablets, 3 desktops */}
</div>
```

---

## 🎨 Design Tokens

### Colors (HSL Format)
```
Primary:      210 65% 25%  (Deep blue)
Accent:       175 60% 40%  (Teal)
Destructive:  0 72% 51%    (Red)
Success:      152 60% 40%  (Green)
Warning:      38 92% 50%   (Amber)
Background:   210 25% 97%  (Light)
Foreground:   215 35% 15%  (Dark)
```

### Using Colors in Components
```jsx
// Using Tailwind utility classes
<div className="bg-primary text-primary-foreground">
<div className="border-border">
<div className="text-muted-foreground">

// Or using CSS variables directly
<div style={{ color: 'hsl(var(--primary))' }}>
```

---

## 🔧 API Response Format

### When backend is connected, expect:

```typescript
interface PredictionResult {
  label: string;          // "PNEUMONIA" or "NORMAL"
  probability: number;    // 0.0 to 1.0 (e.g., 0.87)
  gradcam: string;        // Base64 image: "data:image/png;base64,..."
  overlay: string;        // Base64 image: "data:image/png;base64,..."
}
```

### Current Demo Returns:
- Random 50/50 pneumonia/normal
- Confidence: 82-97%
- Same image for all three visualizations (no real Grad-CAM)
- 3-second delay to simulate processing

---

## 📊 State Management

### Current Flow
```
Index (Main Page)
├── appState: "idle" | "loading" | "results"
├── result: PredictionResult | null
├── originalImage: string (base64)
└── toast notifications for feedback
```

### Important Callbacks
```typescript
handleFileSelect(file)  // Called when file uploaded
handleReset()          // Reset to idle state
```

---

## 🚨 Debugging Tips

### Check console.log
Open browser DevTools (F12) → Console tab

### Check network requests
DevTools → Network tab → Look for `/predict` request to backend

### Check component state
DevTools → React tab → Select component → Check props/state

### Check styling issues
DevTools → Elements tab → Inspect element → Check applied classes

### Hot Reload Issues
- Save file again (sometimes needed)
- Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
- Restart dev server if needed

---

## 📦 Adding Dependencies

### If you need a new package
```bash
npm install package-name
```

Then import in your component:
```typescript
import { Component } from 'package-name';
```

**Current key packages:**
- `react-router-dom` - Navigation
- `react-hook-form` - Forms
- `zod` - Validation
- `tailwindcss` - Styling
- `lucide-react` - Icons
- `sonner` - Toasts

---

## 🔌 Environment Variables

### To use API backend
Create or update environment variable:
```
VITE_API_URL=http://localhost:5000
```

The code automatically uses this:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
```

### Other possible env vars
- `VITE_SUPABASE_URL` - Database URL
- `VITE_SUPABASE_ANON_KEY` - Database key
- Custom API keys for external services

---

## 🐛 Common Issues & Fixes

### Issue: Upload button doesn't work
**Check:** FileUpload component `onFileSelect` prop  
**Fix:** Make sure it's passed from Index.tsx correctly

### Issue: Images show as broken
**Check:** Image path in ResultsDisplay  
**Fix:** Ensure base64 strings have proper format: `data:image/png;base64,xxx`

### Issue: Styles not updating
**Check:** Tailwind configuration  
**Fix:** Restart dev server, or clear browser cache

### Issue: Backend not connecting
**Check:** `VITE_API_URL` environment variable  
**Fix:** Set it to your Flask server URL (default: http://localhost:5000)

### Issue: Toast notifications not showing
**Check:** `useToast()` hook imported correctly  
**Fix:** Make sure `<Toaster />` is in App.tsx (it is)

---

## 📚 File Dependencies

### Which files import what
```
App.tsx
├── All pages (Index.tsx, NotFound.tsx)
├── UI providers (TooltipProvider, Toaster)
└── React Router

Index.tsx
├── Header, HeroSection, FileUpload, LoadingAnalysis, ResultsDisplay, Footer
├── api.ts (predictPneumoniaDemo/predictPneumonia)
└── use-toast hook

FileUpload.tsx
├── ui/button component
└── utils (cn helper)

ResultsDisplay.tsx
├── Multiple lucide-react icons
├── ui/button component
└── utils (cn helper)
```

---

## 🎯 Next Developer Checklist

- [ ] I understand the app flow (upload → loading → results)
- [ ] I can modify component styles (Tailwind classes)
- [ ] I can change colors in index.css
- [ ] I know how to add new components
- [ ] I understand the demo mode vs real backend
- [ ] I can find and edit key files
- [ ] I tested the current running version
- [ ] I read the full CODE_ANALYSIS.md for details

---

## 📞 Quick Links

**Dev Server:** http://localhost:8081/x-ray-vision-clarity/  
**Repository:** SanjeevSharma012/xray-vision-clarity  
**Branch:** v0/sharmasanj99717-3278-280a451c (working branch)  

**Documentation:**
- CODE_ANALYSIS.md - Detailed technical analysis
- PROJECT_SUMMARY.md - Project overview
- QUICK_REFERENCE.md - This file (quick reference)

---

## ✨ Summary

You have a **fully functional React medical AI application** with:
- ✅ Beautiful, responsive UI
- ✅ File upload with validation
- ✅ AI prediction pipeline (demo mode ready)
- ✅ Results visualization
- ✅ Explainability features
- ✅ Dark mode support
- ✅ Accessible design

**Status:** Running and working! Ready for backend integration.

