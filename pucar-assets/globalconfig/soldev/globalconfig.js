    var globalConfigs = (function () {
        var contextPath = "ui";
        var stateTenantId = "pb";
        var configModuleName = "commonUiConfig";
        var centralInstanceEnabled = false;
        var localeRegion = "IN";
        var localeDefault = "en";
        var mdmsContext = "mdms-v2";
        var footerBWLogoURL = "http://10.5.94.229:9000/assests/pucar-assets/digit-footer-bw.png";
        var footerLogoURL = "http://10.5.94.229:9000/assests/pucar-assets/digit-footer.png";
        var digitHomeURL = "https://www.digit.org/";
        var assetS3Bucket = "pucarfilestore";
        var benchId = "BENCH_ID";
        var judgeId = "JUDGE_ID";
        var courtId = "PBPK01";
        var judgeName = "Michael George";
        var mockEnabled = "true";
        var mockESignEnabled = "false";
        var pucarFileStoreBlob = "https://pucarfilestoreuat.blob.core.windows.net"
        var esignUrl = "https://es-staging.cdac.in/esignlevel2/2.1/form/signdoc"
        var WEBSOCKET_ADDRESS = "wss://dristi-kerala-dev.pucar.org/transcription";
        var requiredDocList = "http://minio-filestore.backbone-prod:8080/minio-filestore/v1/files/id?tenantId=pb&fileStoreId=5823408a-edae-4ab3-9c95-f98958fdb294"
        var errorImage = "http://minio-filestore.backbone-prod:8080/minio-filestore/v1/files/id?tenantId=pb&fileStoreId=b7f239f8-3cbf-46a8-8376-2eb5838e2333"
        var emblemBig = "http://minio-filestore.backbone-prod:8080/minio-filestore/v1/files/id?tenantId=pb&fileStoreId=5f153b57-cb05-4a16-ab4e-46bd5b5f38db"
        var onCourtsLogo = "http://minio-filestore.backbone-prod:8080/minio-filestore/v1/files/id?tenantId=pb&fileStoreId=cfab6a6e-8e7c-40cd-970b-733da79807e5"
        var scrutinyCheckList = "http://minio-filestore.backbone-prod:8080/minio-filestore/v1/files/id?tenantId=pb&fileStoreId=96a09f93-307d-411c-8799-b42ee38dd61d" 
        var invalidEmployeeRoles = ["CBO_ADMIN", "ORG_ADMIN", "ORG_STAFF", "SYSTEM"];

        var getConfig = function (key) {
            if (key === "STATE_LEVEL_TENANT_ID") {
                return stateTenantId;
            } else if (key === "ENABLE_SINGLEINSTANCE") {
                return centralInstanceEnabled;
            } else if (key === "DIGIT_FOOTER_BW") {
                return footerBWLogoURL;
            } else if (key === "DIGIT_FOOTER") {
                return footerLogoURL;
            } else if (key === "DIGIT_HOME_URL") {
                return digitHomeURL;
            } else if (key === "S3BUCKET") {
                return assetS3Bucket;
            } else if (key === "CONTEXT_PATH") {
                return contextPath;
            } else if (key === "UICONFIG_MODULENAME") {
                return configModuleName;
            } else if (key === "LOCALE_REGION") {
                return localeRegion;
            } else if (key === "LOCALE_DEFAULT") {
                return localeDefault;
            } else if (key === "MDMS_CONTEXT_PATH") {
                return mdmsContext;
            } else if (key === "INVALIDROLES") {
                return invalidEmployeeRoles;
            } else if (key === "BENCH_ID") {
                return benchId;
            } else if (key === "JUDGE_ID") {
                return judgeId;
            } else if (key === "WEBSOCKET_ADDRESS") {
                return WEBSOCKET_ADDRESS;
            } else if (key === "COURT_ID") {
                return courtId;
            } else if (key === "JUDGE_NAME") {
                return judgeName;
            } else if (key === "MOCKENABLED") {
                return mockEnabled;
            } else if (key === "mockESignEnabled") {
                return mockESignEnabled;
            } else if (key === "ESIGN_URL") {
                return esignUrl;
            } else if (key === "PUCAR_FILESTORE_BLOB") {
                return pucarFileStoreBlob;
            } else if (key === "CASE_FILE_REQUIRED_DOCUMENTS") {
                return requiredDocList;
            } else if (key === "ERROR_IMAGE") {
                return errorImage;
            } else if (key === "EMBLEM_BIG") {
                return emblemBig;
            } else if (key === "ON_COURTS_LOGO") {
                return onCourtsLogo;
            } else if (key === "SCRUTINY_CHECK_LIST") {
                return scrutinyCheckList;
            }
        };

        return {
            getConfig,
        };
    })();
