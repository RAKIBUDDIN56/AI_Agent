---
title: SSO, 2FA, JWT
category: security
tags: [sso, 2fa, jwt]
---

# SSO, 2FA, JWT

Configuration example:

```csharp
configuration.APP.SocialLoginEnable = true;
configuration.APP.SSOClientId = "id";
configuration.APP.SSOClientSecret = "secret";
Authentication:
configuration.Authentication.LoginType = LoginType.LoginDB;


