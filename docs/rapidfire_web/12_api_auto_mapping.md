---
title: REST API Auto Mapping
category: development_features
tags: [api, mapping, rest]
---

# REST API Auto Mapping

Requests & responses are automatically mapped to data models.

Benefits:
- less mapping code
- fewer errors
- faster development

Example:

```csharp
apiResponse = rf.Api.ProcessFetch(apr, null, null);
