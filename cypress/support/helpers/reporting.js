// ==========================================================
// Reporting Helper
// Logs every execution step consistently
// ==========================================================

class Reporting {

    startTest(name) {

        cy.log(`==============================`);
        cy.log(`🚀 TEST : ${name}`);
        cy.log(`==============================`);

    }

    endTest(name) {

        cy.log(`==============================`);
        cy.log(`🏁 END : ${name}`);
        cy.log(`==============================`);

    }

    logStep(step) {

        cy.log(`➡ ${step}`);

    }

    pass(message) {

        cy.log(`✅ ${message}`);

    }

    fail(message) {

        cy.log(`❌ ${message}`);

    }

    info(message) {

        cy.log(`ℹ ${message}`);

    }

}

export default new Reporting();