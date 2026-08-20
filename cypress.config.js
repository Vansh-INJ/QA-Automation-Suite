const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: "https://injin.injtechnologies.com",

    supportFile: "cypress/support/e2e.js",

    specPattern: "cypress/e2e/**/*.cy.js",

    viewportWidth: 1440,
    viewportHeight: 900,

    chromeWebSecurity: false,

    video: true,

    screenshotsFolder: "cypress/screenshots",

    videosFolder: "cypress/videos",
  },

  component: {
    devServer: {
      framework: "react",
      bundler: "vite",
    },
  },
});
