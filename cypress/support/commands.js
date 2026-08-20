import Login from "./actions/login";

Cypress.Commands.add("login", (email, password) => {

    Login.login(email, password);

});