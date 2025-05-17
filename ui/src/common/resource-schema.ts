import {IAMOAuthClient, IAMPolicySubject, IAMRole, IAMScope, IAMUser} from "./models";
import {ResourceSchema} from "./json-schema-definitions";
import {
    compareItemsWith,
    comparePrimitiveValues,
    listFixedItems,
    listItemsFrom,
    createSimpleOptionFromObject,
    createOptionFromPrimitiveValue,
    sendListRequestTo, createComplexOptionFromObject, compareItemsWithKey
} from "./json-schema-utils";
import {
    mustBeAlternativeId,
    minimumSizeOf,
    mustBeEmailAddress,
    securePassword, validUri
} from "./validation";
import {http} from "./http-client";
import {AppConfig} from "./local-models";

export const IAM_ROLE_SCHEMA: ResourceSchema = {
    properties: {
        "id": {
            title: "id",
            label: "ID",
            type: "string",
            required: false,
            isPrimaryKey: true,
            autoGenerationCapability: "full:post",
            readOnly: true,
            hidden: true,
        },
        "name": {
            title: "name",
            label: "Name",
            type: "string",
            required: true,
            constrains: [...mustBeAlternativeId()],
            isReferenceKey: true,
        },
        "description": {
            title: "description",
            label: "Description",
            type: "string",
            required: false,
        },
    }
};

export const IAM_SCOPE_SCHEMA: ResourceSchema = {
    properties: {
        "id": {
            title: "id",
            label: "ID",
            type: "string",
            required: false,
            isPrimaryKey: true,
            autoGenerationCapability: "full:post",
            readOnly: true,
            hidden: true,
        },
        "name": {
            title: "name",
            label: "Name",
            type: "string",
            required: true,
            constrains: [...mustBeAlternativeId()],
            isReferenceKey: true,
        },
        "description": {
            title: "description",
            label: "Description",
            type: "string",
        },
        "sensitive": {
            title: "sensitive",
            label: "Sensitive",
            type: "boolean",
            required: true,
        },
    }
};

type LocalGrantType = {
    id: string;
    description: string;
}

const KNOWN_GRANT_TYPES: LocalGrantType[] = [
    {
        id: "authorization",
        description: "Authorization",
    },
    {
        id: "client_credentials",
        description: "Client Credentials",
    },
    {
        id: "urn:ietf:params:oauth:grant-type:device_code",
        description: "Device Code",
    },
    {
        id: "urn:ietf:params:oauth:grant-type:jwt-bearer",
        description: "User Impersonation",
    },
];

export const IAM_OAUTH_CLIENT_SCHEMA: ResourceSchema = {
    properties: {
        "id": {
            title: "id",
            label: "ID",
            type: "string",
            required: false,
            isPrimaryKey: true,
            autoGenerationCapability: "full:post",
            readOnly: true,
            hidden: true,
        },
        "name": {
            title: "name",
            label: "Client ID",
            type: "string",
            required: true,
            constrains: [...mustBeAlternativeId()],
            isReferenceKey: true,
        },
        "description": {
            title: "description",
            label: "Description",
            type: "string",
        },
        "secret": {
            title: "secret",
            label: "Client Secret",
            type: "string",
            required: true,
            sensitive: true,
            hidden: true,
            autoGenerationCapability: "full:post",
        },
        "audience": {
            title: "audience",
            label: "Audience",
            type: "string",
            required: true,
            autoGenerationCapability: "init:pre",
            autoGenerate: async () => {
                return (await http.sendAndMapAs<AppConfig>("get", "/rest/app-config")).defaultAudienceUri;
            }
        },
        "grant_types": {
            title: "grant_types",
            label: "Grant Types",
            required: true,
            constrains: [minimumSizeOf(1)],
            items: {
                type: "string",
            },
            listRendering: {
                list: "all",
                load: listFixedItems(KNOWN_GRANT_TYPES),
                compare: compareItemsWith("id"),
                normalize: createSimpleOptionFromObject<LocalGrantType, string>("id", "description"),
            }
        },
        "response_types": {
            title: "response_types",
            label: "Response Types",
            required: true,
            constrains: [minimumSizeOf(1)],
            items: {
                type: "string",
            },
            listRendering: {
                list: "all",
                load: listFixedItems(["code"]),
                compare: comparePrimitiveValues(),
                normalize: createOptionFromPrimitiveValue(),
            }
        },
        "scopes": {
            title: "scopes",
            label: "Scopes",
            items: {
                type: "string",
            },
            listRendering: {
                list: "all",
                load: listItemsFrom<IAMScope>("/rest/iam/scopes/"),
                normalize: createSimpleOptionFromObject<IAMScope, string>("name", "description"),
            }
        },
    }
};

export const IAM_USER_SCHEMA: ResourceSchema = {
    properties: {
        "id": {
            title: "id",
            label: "ID",
            type: "string",
            required: false,
            isPrimaryKey: true,
            autoGenerationCapability: "full:post",
            readOnly: true,
            hidden: true,
            style: {
                fontFamily: "monospace",
            }
        },
        "name": {
            title: "name",
            label: "Username",
            type: "string",
            required: true,
            isReferenceKey: true,
            constrains: [...mustBeAlternativeId()],
        },
        "email": {
            title: "email",
            label: "E-mail Address",
            type: "string",
            required: true,
            constrains: [...mustBeEmailAddress()],
        },
        "full_name": {
            title: "full_name",
            label: "Full Name",
            type: "string",
            required: true,
            constrains: [minimumSizeOf(4)],
        },
        "password": {
            title: "password",
            label: "Password",
            type: "string",
            required: true,
            sensitive: true,
            hidden: true,
            constrains: [securePassword()],
        },
        "roles": {
            title: "roles",
            label: "Roles",
            required: true,
            items: {
                type: "string",
            },
            listRendering: {
                list: "all",
                load: listItemsFrom<IAMRole>("/rest/iam/roles/"),
                normalize: createSimpleOptionFromObject<IAMRole, string>("name", "description"),
            }
        },
    }
}


export const IAM_POLICY_SCHEMA: ResourceSchema = {
    properties: {
        "id": {
            title: "id",
            label: "ID",
            type: "string",
            required: false,
            isPrimaryKey: true,
            autoGenerationCapability: "full:post",
            readOnly: true,
            hidden: true,
            style: {
                fontFamily: "monospace",
            }
        },
        "name": {
            title: "name",
            label: "Policy Name",
            type: "string",
            required: true,
            constrains: [...mustBeAlternativeId()],
            isReferenceKey: true,
        },
        "resource": {
            title: "resource",
            label: "Resource URL",
            type: "string",
            required: true,
            constrains: [validUri()],
            autoGenerationCapability: "init:pre",
            autoGenerate: async () => {
                return (await http.sendAndMapAs<AppConfig>("get", "/rest/app-config")).defaultAudienceUri;
            },
        },
        "subjects": {
            title: "subjects",
            label: "Subjects",
            required: true,
            constrains: [minimumSizeOf(1)],
            items: {
                type: "object",
                // TODO handle this type of rendering
                properties: {
                    "subject": {
                        title: "subject",
                        type: "string",
                    },
                    "kind": {
                        title: "kind",
                        type: "string",
                    }
                }
            },
            listRendering: {
                list: "all",
                load: async () => {
                    const subjects: IAMPolicySubject[] = [];

                    for (let client of (await sendListRequestTo<IAMOAuthClient>("/rest/iam/clients/"))) {
                        subjects.push({subject: client.name, kind: "client"});
                    }

                    for (let client of (await sendListRequestTo<IAMOAuthClient>("/rest/iam/roles/"))) {
                        subjects.push({subject: client.name, kind: "role"});
                    }

                    for (let user of (await sendListRequestTo<IAMUser>("/rest/iam/users/"))) {
                        subjects.push({subject: user.name, kind: "user"});
                    }

                    return subjects;
                },
                compare: compareItemsWithKey<IAMPolicySubject>(x => `${x.kind}/${x.subject}`),
                normalize: createComplexOptionFromObject<IAMPolicySubject>(x => `${x.kind}/${x.subject}`),
            }
        },
        "scopes": {
            title: "scopes",
            label: "Scopes",
            required: true,
            constrains: [minimumSizeOf(1)],
            items: {
                type: "string",
            },
            listRendering: {
                list: "all",
                load: listItemsFrom<IAMScope>("/rest/iam/scopes/"),
                normalize: createSimpleOptionFromObject<IAMScope, string>("name", "description"),
            }
        },
    }
}