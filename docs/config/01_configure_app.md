Configure App

The configuration for an application built using the RapidFire framework. The AppConfig class implements the IConfig interface, allowing configuration of various aspects such as application settings, authentication, database setup, and messaging services. This file provides an overview of the configuration structure and its core components.

App Settings (APP)

This section configures high-level system settings:

BusinessModuleName specifies the name of the business module used by the application. In this example, it is set to "Domain", defining the primary functional module.

RootDomain defines the root domain. For local development, it is "localhost".

SocialLoginEnable enables or disables social login support. A value of true allows users to log in using external providers.

DefaultSSO specifies whether Single Sign-On (SSO) is enabled by default.

EnableCSP toggles Content Security Policy (CSP).

AttachmentRoot configures the directory for storing attachments. This configuration uses "files".

AttachmentStoreType defines how attachments are stored. Here, the storage is configured as FileSystem.

AzureBlobAccessKey allows integration with Azure Blob Storage for cloud file access.

AppTitle sets the application title, while AppSlogan defines an optional slogan text shown in the UI.

AppLogo and LoginHomeImage specify paths for branding resources.

AppVersion defines the version displayed in the application.