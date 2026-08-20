import Login from "../../support/actions/login";
import Screenshot from "../../support/helpers/screenshots";

describe("Visual - Login Page", () => {

    beforeEach(() => {

        Login.visit();

        Login.waitUntilLoaded();

    });

    it("should render login page correctly", () => {

        Screenshot.capture("login-page");

    });

});