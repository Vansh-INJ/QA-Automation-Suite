import { LoginSelectors } from "../selectors/login";

class LoginActions {

    visit() {

        cy.visit("/login");

    }

    waitUntilLoaded() {

        cy.get(LoginSelectors.usernameInput)
            .should("be.visible");

        cy.get(LoginSelectors.passwordInput)
            .should("be.visible");

        cy.get(LoginSelectors.loginButton)
            .should("be.visible");

        cy.contains("h1", "Login to your account")
            .should("be.visible");

        cy.contains("Username / Email")
            .should("be.visible");

        cy.contains("Password")
            .should("be.visible");

        cy.contains("Remember me")
            .should("be.visible");

        cy.contains("Forgot your password?")
            .should("be.visible");

        cy.contains("Login with Microsoft365")
            .should("be.visible");

        cy.contains("Created By INJ Technologies")
            .should("be.visible");

    }

    enterUsername(username) {

        cy.get(LoginSelectors.usernameInput)
            .clear()
            .type(username);

    }

    enterPassword(password) {

        cy.get(LoginSelectors.passwordInput)
            .clear()
            .type(password, {
                log: false
            });

    }

    clickLogin() {

        cy.get(LoginSelectors.loginButton)
            .click();

    }

    takeScreenshot(name = "login-page") {

        cy.screenshot(name);

    }

    login(username, password) {

        this.visit();

        this.waitUntilLoaded();

        this.enterUsername(username);

        this.enterPassword(password);

        this.clickLogin();

    }

}

export default new LoginActions();