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
            // hostname: "127.0.0.1"
        }
    },
    // assert: {
    //     assertions: {
    //       'categories:performance': [
    //         'error',
    //         { minScore: 0.9, aggregationMethod: 'median-run' },
    //       ],
    //       'categories:accessibility': [
    //         'error',
    //         { minScore: 1, aggregationMethod: 'pessimistic' },
    //       ],
    //       'categories:best-practices': [
    //         'error',
    //         { minScore: 1, aggregationMethod: 'pessimistic' },
    //       ],
    //       'categories:seo': [
    //         'error',
    //         { minScore: 1, aggregationMethod: 'pessimistic' },
    //       ],
    //     },
    //   },
    upload: {
        target: 'lhci',
        serverBaseUrl: 'https://lhci.example.com',
        token: 'REPLACE-ME-WITH-LHCI-WIZARD-BUILD-TOKEN-VALUE',
        ignoreDuplicateBuildFailure: true,
        allowOverwriteOfLatestBranchBuild: true
    },
    },
};