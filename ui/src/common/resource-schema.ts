import {IAMOAuthClient, IAMPolicySubject, IAMRole, IAMScope, IAMUser} from "./models";
import {JsonSchema} from "./json-schema-definitions";
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

export const IAM_ROLE_SCHEMA: JsonSchema[] = [
    {
        title: "id",
        label: "ID",
        type: "string",
        required: false,
        isPrimaryKey: true,
        autoGenerationCapability: "full:post",
        readOnly: true,
        hidden: true,
    },
    {
        title: "name",
        label: "Name",
        type: "string",
        required: true,
        constrains: [...mustBeAlternativeId()],
        isReferenceKey: true,
    },
    {
        title: "description",
        label: "Description",
        type: "string",
        required: false,
    },
];

export const IAM_SCOPE_SCHEMA: JsonSchema[] = [
    {
        title: "id",
        label: "ID",
        type: "string",
        required: false,
        isPrimaryKey: true,
        autoGenerationCapability: "full:post",
        readOnly: true,
        hidden: true,
    },
    {
        title: "name",
        label: "Name",
        type: "string",
        required: true,
        constrains: [...mustBeAlternativeId()],
        isReferenceKey: true,
    },
    {
        title: "description",
        label: "Description",
        type: "string",
    },
    {
        title: "sensitive",
        label: "Sensitive",
        type: "boolean",
        required: true,
    },
];

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

export const IAM_OAUTH_CLIENT_SCHEMA: JsonSchema[] = [
    {
        title: "id",
        label: "ID",
        type: "string",
        required: false,
        isPrimaryKey: true,
        autoGenerationCapability: "full:post",
        readOnly: true,
        hidden: true,
    },
    {
        title: "name",
        label: "Client ID",
        type: "string",
        required: true,
        constrains: [...mustBeAlternativeId()],
        isReferenceKey: true,
    },
    {
        title: "description",
        label: "Description",
        type: "string",
    },
    {
        title: "secret",
        label: "Client Secret",
        type: "string",
        required: true,
        sensitive: true,
        hidden: true,
        autoGenerationCapability: "full:post",
    },
    {
        title: "audience",
        label: "Audience",
        type: "string",
        required: true,
        constrains: [validUri()],
        autoGenerationCapability: "init:pre",
        autoGenerate: async () => {
            return (await http.sendAndMapAs<AppConfig>("get", "/rest/app-config")).defaultAudienceUri;
        }
    },
    {
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
    {
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
    {
        title: "scopes",
        label: "Scopes",
        items: {
            type: "string",
        },
        listRendering: {
            list: "all",
            load: listItemsFrom<IAMScope>("/rest/scopes/"),
            normalize: createSimpleOptionFromObject<IAMScope, string>("name", "description"),
        }
    },
];

export const IAM_USER_SCHEMA: JsonSchema[] = [
    {
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
    {
        title: "name",
        label: "Username",
        type: "string",
        required: true,
        isReferenceKey: true,
        constrains: [...mustBeAlternativeId()],
    },
    {
        title: "email",
        label: "E-mail Address",
        type: "string",
        required: true,
        constrains: [...mustBeEmailAddress()],
    },
    {
        title: "full_name",
        label: "Full Name",
        type: "string",
        required: true,
        constrains: [minimumSizeOf(4)],
    },
    {
        title: "password",
        label: "Password",
        type: "string",
        required: true,
        sensitive: true,
        hidden: true,
        constrains: [securePassword()],
    },
    {
        title: "roles",
        label: "Roles",
        required: true,
        items: {
            type: "string",
        },
        listRendering: {
            list: "all",
            load: listItemsFrom<IAMRole>("/rest/roles/"),
            normalize: createSimpleOptionFromObject<IAMRole, string>("name", "description"),
        }
    },
]

export const IAM_POLICY_SCHEMA: JsonSchema[] = [
    {
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
    {
        title: "name",
        label: "Policy Name",
        type: "string",
        required: true,
        constrains: [...mustBeAlternativeId()],
        isReferenceKey: true,
    },
    {
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
    {
        title: "subjects",
        label: "Subjects",
        required: true,
        constrains: [minimumSizeOf(1)],
        items: {
            type: "object",
            // TODO handle this type of rendering
            properties: [
                {
                    title: "subject",
                    type: "string",
                },
                {
                    title: "kind",
                    type: "string",
                }
            ]
        },
        listRendering: {
            list: "all",
            load: async () => {
                const subjects: IAMPolicySubject[] = [];

                for (let client of (await sendListRequestTo<IAMOAuthClient>("/rest/clients/"))) {
                    subjects.push({subject: client.name, kind: "client"});
                }

                for (let client of (await sendListRequestTo<IAMOAuthClient>("/rest/roles/"))) {
                    subjects.push({subject: client.name, kind: "role"});
                }

                for (let user of (await sendListRequestTo<IAMUser>("/rest/users/"))) {
                    subjects.push({subject: user.name, kind: "user"});
                }

                return subjects;
            },
            compare: compareItemsWithKey<IAMPolicySubject>(x => `${x.kind}/${x.subject}`),
            normalize: createComplexOptionFromObject<IAMPolicySubject>(x => `${x.kind}/${x.subject}`),
        }
    },
    {
        title: "scopes",
        label: "Scopes",
        required: true,
        constrains: [minimumSizeOf(1)],
        items: {
            type: "string",
        },
        listRendering: {
            list: "all",
            load: listItemsFrom<IAMScope>("/rest/scopes/"),
            normalize: createSimpleOptionFromObject<IAMScope, string>("name", "description"),
        }
    },
]