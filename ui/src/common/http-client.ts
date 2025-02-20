type SendOptions = {
    noAuth?: boolean;
    okStatusCodes?: number[];
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
    async send(method: "get" | "post" | "put" | "delete", url: string, options?: SendOptions): Promise<Response> {
        const noAuth = options?.noAuth || false;
        let headers: { [key: string]: string } = {};
        let fetchOptions: any = {
            method: method,
        };

        if (!noAuth) {
            headers['Authorization'] = `Bearer ${sessionStorage.getItem("access_token")}`;
        }

        if (options?.headers) {
            headers = {...headers, ...options.headers};
        }

        if (options?.json) {
            headers = {...headers, "Content-Type": "application/json"};
            fetchOptions.body = JSON.stringify(options.json);
        }

        fetchOptions.headers = headers;

        return fetch(url, fetchOptions)
    }

    async simpleSend<T>(method: "get" | "post" | "put" | "delete", url: string, options?: SendOptions): Promise<T> {
        const response = await this.send(method, url, options);
        const responseText = await response.text();

        if ((options?.okStatusCodes || [200]).includes(response.status)) {
            return JSON.parse(responseText) as T;
        } else {
            throw new HttpError(response.status, responseText);
        }
    }
}

export const http = new HttpClient();