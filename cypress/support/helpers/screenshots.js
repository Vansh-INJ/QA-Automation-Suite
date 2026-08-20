class ScreenshotHelper {

    capture(pageName) {

        cy.document().then((doc) => {

            // Wait until fonts are loaded
            return doc.fonts.ready;

        });

        // Wait for animations to finish
        cy.wait(500);

        // Capture the entire page
        cy.screenshot(pageName, {

            capture: "fullPage"

        });

    }

}

export default new ScreenshotHelper();