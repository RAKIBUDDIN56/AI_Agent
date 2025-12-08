---
title: UI Components
category: ui_framework
tags: [components, ui, controls]
---

# UI Components

RapidFire provides **88+ UI components** used frequently in industry.

## Example

```csharp
style.Border.All("#000", 2, BorderStyleRF.Dashed);
Components are:

simple to implement

customizable

---


```md
---
title: Styling & Theming
category: ui_framework
tags: [style, theme, ui]
---

# Styling & Theming

Developers can:
- build fully custom themes
- or select pre-made themes

Control:
- colors
- typography
- component styling
- layouts

Example:

```csharp
configuration.APP.AppStyle = new AppStyleRF()
{
    AppTheme = AppThemeRF.Classic,
    AppStyle = new AppStyle()
};


---



```md
---
title: Templates
category: ui_framework
tags: [templates, classic, modern, metro]
---

# Templates

RapidFire includes **3 pre-built UI templates**:

- Classic (default)
- Modern
- Metro

Templates can be switched using:
- AppConfig
- CLI parameter

