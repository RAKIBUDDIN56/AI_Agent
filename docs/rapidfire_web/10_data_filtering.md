---
title: Data Filtering
category: development_features
tags: [filter, grid, data]
---

# Data Filtering

Define filters once → applied everywhere.

Example:

```razor
<FilterRF @bind-Model="filter">
    <InputRF @bind-Value="context.Title" Label="Title"/>
</FilterRF>

Connected grid:
<GridRF Model="ProductView"
    Filter="w => w.Title.Contains(filter.Title)">
</GridRF>

