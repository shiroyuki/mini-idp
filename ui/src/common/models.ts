export interface IAMScope {
    id?: string | null;
    name: string;
    description?: string | null;
    sensitive?: boolean | null;
    fixed?: boolean | null;
}

export interface IAMRole {
    id?: string | null;
    name: string;
    description?: string | null;
    fixed?: boolean | null;
}

export interface IAMUser {
    id?: string | null;
    name: string;
    password?: string | null;
    email: string;
    full_name?: string;
    roles: string[];
}

export interface IAMOAuthClient {
    id?: string | null;
    name: string;
    secret?: string | null;
    audience: string;
    grant_types: string[];
    response_types: string[];
    scopes: string[];
    extras: Record<string, any>;
    description?: string;
}

export interface IAMPolicySubject {
    subject: string;
    kind: string; // should match 'client' | 'user' | 'role'
}

export interface IAMPolicy {
    id?: string | null;
    name: string;
    resource: string;
    subjects: IAMPolicySubject[];
    scopes: string[];
    fixed?: boolean | null;
}
