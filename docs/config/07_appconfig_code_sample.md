using Domain.Contexts;
using Domain.Handlers;
using RapidFireLib.Lib.Api;
using RapidFireLib.Lib.Core;
using RapidFireUI;
using RapidFireUI.Style;

namespace Web.Config
{
    public class AppConfig : IConfig
    {
        public void Configure(Configuration configuration)
        {
            configuration.APP.BusinessModuleName = "Domain";
            configuration.APP.RootDomain = "localhost";
            configuration.APP.EnableCSP = false;
            configuration.APP.AttachmentRoot = "files";
            configuration.APP.AttachmentStoreType = AttachmentStoreType.FileSystem;
            configuration.APP.AzureBlobAccessKey = "";
            configuration.APP.AppTitle = "DocRF";
            configuration.APP.AppSlogan = "Preparing Documentation";
            configuration.APP.AppLogo = "docRF-logo.png";
            configuration.APP.LoginHomeImage = "bg-4.jpg";
            configuration.APP.AppVersion = "1.0";

            configuration.APP.SocialLoginEnable = true;
            configuration.APP.DefaultSSO = false;
            configuration.APP.SSOClientId = "id";
            configuration.APP.SSOClientSecret = "secret";
            configuration.APP.SSOAuthority = "https://login.microsoftonline.com/auth";

            configuration.APP.AppStyle = new AppStyleRF()
            {
                AppTheme = AppThemeRF.Classic,
                AppStyle = new AppStyle()
            };

            configuration.Authentication.LoginType =
                RapidFireLib.Lib.Authintication.LoginType.LoginDB;

            configuration.DB.DefaultDbContext = new DefaultContext(SAASType.NoSaas);
            configuration.DB.CheckTablePermission = false;
            configuration.DB.DynamicViewModelHandlers =
                new IDbHandler[] { new UpdateCommonFields() };

            configuration.Messaging.Email = new ConfigEmailAuth
            {
                Username = "email@mail.com",
                Password = "epass"
            };

            configuration.Messaging.FCM.ConfigJsonPath = "firebase-config.json";
            configuration.Messaging.FChat.BasePath =
                "https://*****83-default-rtdb.asia-southeast1.firebasedatabase.app/";
            configuration.Messaging.FChat.AuthSecret = "jVi1z*********************8gDfUOos";
        }
    }
}
