module.exports = {
    ci: {
    collect: {
        url: "https://www.example.com",
        maxAutodiscoverUrls: 3,
        numberOfRuns: 2,
        settings: {
            chromeFlags: "--no-sandbox",
            onlyCategories: ["performance", "best-practices", "accessibility", "seo"],
            skipAudits: ['uses-http2', 'uses-long-cache-ttl', 'link-text']
        }
    },
    upload: {
        target: 'lhci',
        serverBaseUrl: 'https://lighthouse.example.com',
        token: 'example-000-example',
        ignoreDuplicateBuildFailure: true,
        allowOverwriteOfLatestBranchBuild: true
    },
    },
};