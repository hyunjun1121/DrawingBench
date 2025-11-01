# Drawing Application UI Coordinates

This document describes the exact screen coordinates of all UI elements in the drawing application. LLMs must use these coordinates to interact with the application through mouse actions.

## Application Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Screen Coordinates (0, 0)                        │
├──────┬──────────────────────────────────────────────────────────────────┤
│      │  Menu Bar (y: 0-50)                                              │
│      ├──────────────────────────────────────────────────────────────────┤
│ Tool │                                                                   │
│ Bar  │                    Canvas Area                                   │
│      │                  (1000 x 700 pixels)                             │
│ (x:  │                                                                   │
│ 0-80)│  Canvas starts at screen coordinates: (90, 70)                   │
│      │                                                                   │
│      │                                                                   │
└──────┴──────────────────────────────────────────────────────────────────┘
```

## Canvas Coordinates

**Important**: The canvas drawing area starts at screen coordinates (90, 70).

- **Canvas Size**: 1000 x 700 pixels
- **Canvas Top-Left**: Screen (90, 70)
- **Canvas Bottom-Right**: Screen (1090, 770)
- **Canvas Center**: Screen (590, 420) = Canvas (500, 350)

**Coordinate Conversion**:
- Screen X = Canvas X + 90
- Screen Y = Canvas Y + 70

## UI Element Coordinates

### Left Toolbar (Tools)

All tool buttons are 70x70 pixels, centered at x=35.

| Tool    | Center Coordinates | Bounds (x1, y1, x2, y2) |
|---------|-------------------|-------------------------|
| Pen     | (35, 45)          | (0, 10, 70, 80)        |
| Eraser  | (35, 125)         | (0, 90, 70, 160)       |
| Fill    | (35, 205)         | (0, 170, 70, 240)      |

**Example**: To select the Pen tool:
```json
{"action": "moveTo", "x": 35, "y": 45}
{"action": "click"}
```

### Top Menu Bar - Pen Size Buttons

All size buttons are 40x40 pixels, centered at y=25.

| Size | Center Coordinates | Visual |
|------|--------------------|--------|
| 2px  | (145, 25)          | Small  |
| 5px  | (195, 25)          | Medium |
| 10px | (245, 25)          | Large  |
| 20px | (295, 25)          | XLarge |

**Example**: To select 10px pen size:
```json
{"action": "moveTo", "x": 245, "y": 25}
{"action": "click"}
```

### Top Menu Bar - Color Palette

All color buttons are 40x40 pixels, centered at y=25, starting from x=405.

| Color   | Hex Code | Center Coordinates | Offset from start |
|---------|----------|-------------------|-------------------|
| Black   | #000000  | (405, 25)         | 0                 |
| Red     | #FF0000  | (453, 25)         | +48               |
| Green   | #00FF00  | (501, 25)         | +96               |
| Blue    | #0000FF  | (549, 25)         | +144              |
| Yellow  | #FFFF00  | (597, 25)         | +192              |
| Magenta | #FF00FF  | (645, 25)         | +240              |
| Cyan    | #00FFFF  | (693, 25)         | +288              |
| White   | #FFFFFF  | (741, 25)         | +336              |

**Example**: To select red color:
```json
{"action": "moveTo", "x": 453, "y": 25}
{"action": "click"}
```

## Drawing Actions

### Available Mouse Actions

1. **moveTo**: Move cursor to specified coordinates
   ```json
   {"action": "moveTo", "x": 500, "y": 400}
   ```

2. **click**: Single click at current or specified position
   ```json
   {"action": "click"}
   {"action": "click", "x": 100, "y": 100}
   ```

3. **mouseDown**: Press and hold mouse button (start drawing)
   ```json
   {"action": "mouseDown"}
   {"action": "mouseDown", "x": 200, "y": 300}
   ```

4. **mouseUp**: Release mouse button (stop drawing)
   ```json
   {"action": "mouseUp"}
   ```

### Drawing Workflow Examples

#### Example 1: Draw a red circle outline

```json
[
  {"action": "moveTo", "x": 453, "y": 25},
  {"action": "click"},
  {"action": "moveTo", "x": 245, "y": 25},
  {"action": "click"},
  {"action": "moveTo", "x": 590, "y": 420},
  {"action": "mouseDown"},
  {"action": "moveTo", "x": 640, "y": 420},
  {"action": "moveTo", "x": 665, "y": 445},
  {"action": "moveTo", "x": 665, "y": 495},
  {"action": "moveTo", "x": 640, "y": 520},
  {"action": "moveTo", "x": 590, "y": 520},
  {"action": "moveTo", "x": 540, "y": 520},
  {"action": "moveTo", "x": 515, "y": 495},
  {"action": "moveTo", "x": 515, "y": 445},
  {"action": "moveTo", "x": 540, "y": 420},
  {"action": "moveTo", "x": 590, "y": 420},
  {"action": "mouseUp"}
]
```

**Step-by-step**:
1. Click red color button at (453, 25)
2. Click large size at (245, 25)
3. Move to canvas center (590, 420)
4. Press mouse down
5. Move in circular path
6. Return to start
7. Release mouse

#### Example 2: Draw a simple house

```json
[
  {"action": "moveTo", "x": 35, "y": 45},
  {"action": "click"},
  {"action": "moveTo", "x": 195, "y": 25},
  {"action": "click"},
  {"action": "moveTo", "x": 405, "y": 25},
  {"action": "click"},
  {"action": "moveTo", "x": 390, "y": 470},
  {"action": "mouseDown"},
  {"action": "moveTo", "x": 690, "y": 470},
  {"action": "moveTo", "x": 690, "y": 670},
  {"action": "moveTo", "x": 390, "y": 670},
  {"action": "moveTo", "x": 390, "y": 470},
  {"action": "mouseUp"},
  {"action": "moveTo", "x": 390, "y": 470},
  {"action": "mouseDown"},
  {"action": "moveTo", "x": 540, "y": 320},
  {"action": "moveTo", "x": 690, "y": 470},
  {"action": "mouseUp"}
]
```

**Step-by-step**:
1. Select pen tool
2. Select medium size (5px)
3. Select black color
4. Draw square (walls): start at bottom-left, draw rectangle
5. Draw triangle (roof): from top-left to peak to top-right

#### Example 3: Fill a shape with color

```json
[
  {"action": "moveTo", "x": 35, "y": 45},
  {"action": "click"},
  {"action": "moveTo", "x": 405, "y": 25},
  {"action": "click"},
  {"action": "moveTo", "x": 400, "y": 400},
  {"action": "mouseDown"},
  {"action": "moveTo", "x": 500, "y": 400},
  {"action": "moveTo", "x": 500, "y": 500},
  {"action": "moveTo", "x": 400, "y": 500},
  {"action": "moveTo", "x": 400, "y": 400},
  {"action": "mouseUp"},
  {"action": "moveTo", "x": 35, "y": 205},
  {"action": "click"},
  {"action": "moveTo", "x": 597, "y": 25},
  {"action": "click"},
  {"action": "moveTo", "x": 450, "y": 450},
  {"action": "click"}
]
```

**Step-by-step**:
1. Select pen tool
2. Select black color
3. Draw square outline (canvas coords: 310,330 to 410,430)
4. Select fill tool
5. Select yellow color
6. Click inside the square to fill

## Tips for LLM Usage

### 1. Always Set Tool and Properties First

Before drawing, always:
1. Select the appropriate tool (pen, eraser, fill)
2. Select pen size
3. Select color

### 2. Canvas Coordinate Conversion

Remember to add offsets when converting canvas coordinates to screen coordinates:
- To draw at canvas position (100, 200), use screen position (190, 270)

### 3. Drawing Smooth Curves

For smooth curves, use many small moveTo steps while mouseDown:
```json
[
  {"action": "mouseDown", "x": 100, "y": 100},
  {"action": "moveTo", "x": 105, "y": 102},
  {"action": "moveTo", "x": 110, "y": 106},
  {"action": "moveTo", "x": 115, "y": 112},
  ...
  {"action": "mouseUp"}
]
```

### 4. Common Patterns

**Draw a line**:
```json
[
  {"action": "mouseDown", "x": x1, "y": y1},
  {"action": "moveTo", "x": x2, "y": y2},
  {"action": "mouseUp"}
]
```

**Draw a rectangle**:
```json
[
  {"action": "mouseDown", "x": x1, "y": y1},
  {"action": "moveTo", "x": x2, "y": y1},
  {"action": "moveTo", "x": x2, "y": y2},
  {"action": "moveTo", "x": x1, "y": y2},
  {"action": "moveTo", "x": x1, "y": y1},
  {"action": "mouseUp"}
]
```

**Draw a dot**:
```json
[
  {"action": "click", "x": x, "y": y}
]
```

### 5. Complex Shapes

For complex shapes like circles, stars, or irregular shapes:
1. Calculate the path points mathematically
2. Convert to screen coordinates (add canvas offset)
3. Use mouseDown → multiple moveTo → mouseUp

### 6. Multi-color Drawings

When drawing with multiple colors:
1. Complete all drawing with one color
2. Switch color by clicking color button
3. Continue with next color
4. Repeat as needed

## Error Prevention

1. **Always check coordinates are within bounds**:
   - Canvas X: 90 to 1090
   - Canvas Y: 70 to 770

2. **Don't forget to release mouse**:
   - Always pair mouseDown with mouseUp

3. **Set tools before drawing**:
   - Tool selection before drawing actions

4. **Avoid rapid coordinate changes**:
   - For smooth lines, increment coordinates gradually

## Testing

To test if coordinates are correct, try this simple test:
```json
[
  {"action": "moveTo", "x": 453, "y": 25},
  {"action": "click"},
  {"action": "moveTo", "x": 590, "y": 420},
  {"action": "click"}
]
```

This should:
1. Select red color
2. Draw a red dot in the center of canvas
