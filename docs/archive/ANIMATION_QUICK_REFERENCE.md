# 🎨 Animation Quick Reference

Schnell-Referenz für Scroll-Animationen auf SIGMACODE Blockchain Forensics.

---

## 📦 Import

```tsx
import { motion } from 'framer-motion'
import { 
  fadeUp,
  fadeIn,
  slideInLeft,
  slideInRight,
  scaleUp,
  iconBounce,
  staggerContainer,
  staggerItem,
  defaultViewport,
  earlyViewport,
  cardHoverEffect,
  buttonHoverEffect
} from '@/utils/animations'

import { AnimatedCounter, StatCounter } from '@/components/ui/AnimatedCounter'
```

---

## 🔥 Häufigste Patterns

### 1. **Einfache Section (Fade + Slide)**
```tsx
<motion.div 
  variants={fadeUp}
  initial="initial"
  whileInView="whileInView"
  viewport={defaultViewport}
>
  <h2>Section Title</h2>
  <p>Content...</p>
</motion.div>
```

### 2. **Cards mit Stagger (Liste)**
```tsx
<motion.div 
  variants={staggerContainer}
  initial="initial"
  whileInView="whileInView"
  viewport={defaultViewport}
  className="grid grid-cols-3 gap-6"
>
  {items.map(item => (
    <motion.div
      key={item.id}
      variants={staggerItem}
      whileHover={cardHoverEffect}
    >
      <Card>{item.content}</Card>
    </motion.div>
  ))}
</motion.div>
```

### 3. **Stats mit Counter**
```tsx
{/* Einfach */}
<AnimatedCounter value="$12.6B+" duration={2000} />

{/* Mit Label (empfohlen) */}
<StatCounter 
  value="100+" 
  label="Blockchains"
  valueClassName="text-4xl font-bold text-primary"
  labelClassName="text-sm text-muted-foreground"
/>
```

### 4. **Icon mit Spring-Animation**
```tsx
<motion.div
  variants={iconBounce}
  initial="initial"
  whileInView="whileInView"
  viewport={earlyViewport}
>
  <Shield className="h-8 w-8 text-primary" />
</motion.div>
```

### 5. **Button mit Hover**
```tsx
<motion.div whileHover={buttonHoverEffect}>
  <Button>Click Me</Button>
</motion.div>
```

---

## 🎯 Viewport-Settings

```tsx
// Standard (meiste Fälle)
viewport={defaultViewport}
// → once: true, margin: '-100px', amount: 0.2

// Früher triggern (Hero-Sections)
viewport={earlyViewport}
// → once: true, margin: '-50px', amount: 0.1

// Custom
viewport={{ once: true, margin: '-150px', amount: 0.3 }}
```

---

## ⚡ Performance-Tipps

### DO ✅
```tsx
// Viewport-triggered (nur einmal)
<motion.div viewport={{ once: true }} />

// Transform/Opacity (GPU-accelerated)
<motion.div animate={{ y: 0, opacity: 1 }} />

// Stagger für Listen
<motion.div variants={staggerContainer}>...</motion.div>
```

### DON'T ❌
```tsx
// Ohne viewport (animiert immer)
<motion.div animate={{ y: 0 }} />  // ❌ Performance-Issue

// Width/Height (Layout-Thrashing)
<motion.div animate={{ width: 100 }} />  // ❌ Laggy

// Zu viele Elemente ohne Stagger
{items.map(item => <motion.div key={item.id} />)}  // ❌ Gleichzeitig
```

---

## 🎨 Custom Animations

### Eigene Variant erstellen
```tsx
const customAnimation = {
  initial: { opacity: 0, scale: 0.8, rotate: -10 },
  whileInView: { 
    opacity: 1, 
    scale: 1, 
    rotate: 0,
    transition: { 
      duration: 0.6,
      type: 'spring',
      stiffness: 100
    }
  }
}

<motion.div variants={customAnimation} initial="initial" whileInView="whileInView" />
```

### Sequenzielle Animation
```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ 
    duration: 0.6,
    delay: 0.2  // Wartet 0.2s
  }}
/>
```

---

## 🔢 Counter-Formate

```tsx
// Verschiedene Formate (alle unterstützt)
<AnimatedCounter value="$12.6B+" />   // → zählt von $0.0B+ bis $12.6B+
<AnimatedCounter value="100+" />      // → zählt von 0+ bis 100+
<AnimatedCounter value="99.9%" />     // → zählt von 0.0% bis 99.9%
<AnimatedCounter value="< 100ms" />   // → zählt von < 0ms bis < 100ms
<AnimatedCounter value="ISO 27001" /> // → zeigt direkt (keine Zahl)
```

---

## 🎬 Animation-Sequenzen (Header)

```tsx
// Hero-Header mit sequenzieller Animation
<motion.div
  initial={{ opacity: 0, y: 30 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.6 }}
>
  {/* Badge */}
  <motion.div
    initial={{ opacity: 0, scale: 0.9 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ duration: 0.5, delay: 0.2 }}
  >
    <Badge>New</Badge>
  </motion.div>
  
  {/* Title */}
  <motion.h1
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.6, delay: 0.3 }}
  >
    Title
  </motion.h1>
  
  {/* Subtitle */}
  <motion.p
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ duration: 0.6, delay: 0.4 }}
  >
    Subtitle
  </motion.p>
  
  {/* CTA */}
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.6, delay: 0.5 }}
  >
    <Button>Get Started</Button>
  </motion.div>
</motion.div>
```

---

## 📱 Responsive Animations

```tsx
// Mobile: Schnellere Animationen
const isMobile = window.innerWidth < 768

<motion.div
  variants={fadeUp}
  transition={{ 
    duration: isMobile ? 0.4 : 0.6  // Schneller auf Mobile
  }}
/>
```

---

## 🌙 Dark-Mode Support

**Alle Animationen sind Dark-Mode-ready!** Keine Anpassungen nötig.

```tsx
// Funktioniert automatisch
<motion.div variants={fadeUp}>
  <div className="bg-white dark:bg-slate-800">
    Content
  </div>
</motion.div>
```

---

## 🐛 Troubleshooting

### Animation triggert nicht?
```tsx
// ❌ Falsch
<motion.div variants={fadeUp} />

// ✅ Richtig
<motion.div 
  variants={fadeUp} 
  initial="initial"           // ← wichtig!
  whileInView="whileInView"  // ← wichtig!
  viewport={defaultViewport}  // ← wichtig!
/>
```

### Animation wiederholt sich?
```tsx
// ❌ once: false (default bei viewport)
viewport={{ once: false }}

// ✅ once: true (empfohlen)
viewport={{ once: true }}
```

### Zu langsam/schnell?
```tsx
// Adjust duration
transition={{ duration: 0.4 }}  // Schneller
transition={{ duration: 0.8 }}  // Langsamer
```

---

## 📊 Cheat Sheet

| Animation | Use-Case | Duration | Easing |
|-----------|----------|----------|--------|
| `fadeUp` | Sections, Headers | 0.6s | easeOutQuart |
| `fadeIn` | Text, Images | 0.6s | easeOut |
| `slideInLeft` | Side-Panels | 0.6s | spring (80) |
| `scaleUp` | Modals, Popups | 0.5s | spring (100) |
| `iconBounce` | Icons, Badges | 0.4s | spring (200) |
| `staggerContainer` | Lists, Grids | - | - |
| `staggerItem` | List-Items | 0.5s | easeOut |

---

## ✨ Best Practices

1. **Immer `once: true`** - Performance!
2. **Viewport margin: -100px** - Animiert bevor sichtbar
3. **Stagger-Delays: 0.1s** - Nicht zu schnell, nicht zu langsam
4. **Transform > Width/Height** - GPU-accelerated
5. **Mobile: Kürzere Durations** - Schnellere UX

---

## 🚀 Copy-Paste-Templates

### Template 1: Feature-Section
```tsx
<motion.section
  variants={fadeUp}
  initial="initial"
  whileInView="whileInView"
  viewport={defaultViewport}
  className="py-20"
>
  <h2 className="text-4xl font-bold mb-4">Features</h2>
  <p className="text-muted-foreground mb-12">Description</p>
  
  <motion.div
    variants={staggerContainer}
    className="grid grid-cols-3 gap-6"
  >
    {features.map(feature => (
      <motion.div
        key={feature.id}
        variants={staggerItem}
        whileHover={cardHoverEffect}
      >
        <Card>
          <CardHeader>
            <motion.div variants={iconBounce}>
              <feature.icon className="h-8 w-8" />
            </motion.div>
            <CardTitle>{feature.title}</CardTitle>
          </CardHeader>
          <CardContent>{feature.description}</CardContent>
        </Card>
      </motion.div>
    ))}
  </motion.div>
</motion.section>
```

### Template 2: Stats-Section
```tsx
<motion.section
  variants={fadeUp}
  initial="initial"
  whileInView="whileInView"
  viewport={defaultViewport}
  className="py-12 bg-muted/30"
>
  <div className="grid grid-cols-4 gap-8 text-center">
    {stats.map(stat => (
      <div key={stat.id}>
        <AnimatedCounter 
          value={stat.value}
          className="text-4xl font-bold text-primary mb-2"
        />
        <div className="text-sm text-muted-foreground">
          {stat.label}
        </div>
      </div>
    ))}
  </div>
</motion.section>
```

---

**Fragen?** Siehe `SCROLL_ANIMATIONS_COMPLETE.md` für Details!
