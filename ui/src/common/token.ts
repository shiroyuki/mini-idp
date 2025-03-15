import {storage} from "./storage";

import {GenericModel} from "./definitions";

export interface JwtClaims extends GenericModel {
    sub: string;
    scope: string;
}

export class Token {
    constructor(protected rawToken: string) {}

    get original() {
        return this.rawToken;
    }

    get claims() {
        const encodedClaims = this.rawToken.split(".")[1];
        return JSON.parse(atob(encodedClaims)) as JwtClaims;
    }

    get scopes(): string[] {
        return this.claims.scope.length > 0
            ? this.claims.scope.split(/\s+/)
            : [];
    }
}

export const getAccessToken = () => {
    const token = storage.get("access_token");
    return token !== null ? new Token(token) : null;
}