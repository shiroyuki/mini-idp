import {storage} from "./storage";
import {getAccessToken} from "./token";

export type ClientOptions = {
    authRequired?: boolean;
    noAuth?: boolean;
    okStatusCodes?: number[];
    /**
     * Handle error
     *
     * NOTE: Not used in the advanced mode.
     *
     * @param response
     */
    handleError?: (response: Response) => void;
    headers?: { [key: string]: string },
    json?: any,
};

export class HttpError extends Error {
    status: number;
    body: string;

    constructor(status: number, body: string) {
        super(`HTTP ${status}: ${body}`);
        this.status = status;
        this.body = body;
    }
}

export class HttpClient {
    /**
     * Send a HTTP request.
     */
    async send(method: "get" | "post" | "put" | "delete", url: string, options?: ClientOptions): Promise<Response> {
        const authRequired = options?.authRequired || false;
        const noAuth = options?.noAuth || false;
        let headers: { [key: string]: string } = {};
        let fetchOptions: any = {
            method: method,
        };

        if (!noAuth) {
            const accessToken = getAccessToken();
            if (accessToken !== null) {
                headers['Authorization'] = `Bearer ${accessToken.original}`;
            } else {
                if (authRequired) {
                    throw new Error(`${method} ${url} requires the access token but it is UNAVAILABLE.`);
                } else {
                    console.log(`The ${method} ${url} is submitted without access token.`)
                }
            }
        }

        if (options?.headers) {
            headers = {...headers, ...options.headers};
        }

        if (options?.json) {
            headers = {...headers, "Content-Type": "application/json"};
            fetchOptions.body = JSON.stringify(options.json);
        }

        fetchOptions.headers = headers;

        return fetch(url, fetchOptions);
    }

    /**
     * Send a request and automatically map the response.
     */
    async sendAndMapAs<T>(method: "get" | "post" | "put" | "delete", url: string, options?: ClientOptions): Promise<T> {
        const response = await this.send(method, url, options);

        if ((options?.okStatusCodes || [200]).includes(response.status)) {
            const responseText = await response.text();
            return JSON.parse(responseText) as T;
        } else {
            if (options?.handleError) {
                options?.handleError(response);
            }

            const responseText = await response.text();
            throw new HttpError(response.status, responseText || '(no response body)');
        }
    }
}

export const http = new HttpClient();