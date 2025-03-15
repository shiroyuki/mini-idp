import {http, HttpError} from "./http-client";
import {IAMRole, IAMScope} from "./models";
import {CSSProperties} from "react";
import {ejectToLoginScreen} from "./helpers";

type JsonSchemaDataType = "string" | "number" | "integer" | "float" | "boolean" | "object";

export type ListTransformedOption = {
    checked: boolean;
    label?: string;
    value: string;
};

type LoadedItemToSelectionOptionTransformer = (selectedItems: any[], iteratingLoadedItem: any) => ListTransformedOption;

export type ListRenderingOptions = {
    list: "selected-only" | "all"; // default: all
    load: () => Promise<any[]>;
    maxSelections?: number; // default: -1 (no limit)
    minSelections?: number; // default: 0 (optional) or 1 (required)
    compare?: (a: any, b: any) => -1 | 0 | 1;
    transformForEditing: LoadedItemToSelectionOptionTransformer;
};

/**
 * JSON Schema (custom)
 */
export type ResourceSchema = {
    ///// Standard JSON Schema /////
    title?: string;
    type?: JsonSchemaDataType;
    required?: boolean;
    items?: ResourceSchema;
    ///// Custom properties /////
    label?: string;
    readOnly?: boolean;
    hidden?: boolean;
    default?: any;
    /**
     * The capability for auto-generation
     *
     * - full:pre = fully automated by the UI
     * - full:post = fully automated by the backend
     * - semi = automated by the backend if not available.
     * - UNDEFINED = no automation available
     */
    autoGenerationCapability?: "full:pre" | "full:post" | "semi";
    autoGenerate?: () => any;
    isPrimaryKey?: boolean;
    isReferenceKey?: boolean;
    ///// For sensitive information, e.g. password /////
    requireRepeat?: boolean;
    sensitive?: boolean;
    ///// For rendering list /////
    listRendering?: ListRenderingOptions;
    ///// For minimal customization /////
    className?: string;
    style?: CSSProperties;
    ///// For custom rendering /////
    render?: (schema: ResourceSchema, data: any) => any;
};

export const IAM_ROLE_SCHEMA: ResourceSchema[] = [
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
        isReferenceKey: true,
    },
    {
        title: "description",
        label: "Description",
        type: "string",
        required: false,
    },
];

export const IAM_SCOPE_SCHEMA: ResourceSchema[] = [
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

export const IAM_OAUTH_CLIENT_SCHEMA: ResourceSchema[] = [
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
    },
    {
        title: "audience",
        label: "Audience",
        type: "string",
    },
    {
        title: "grant_types",
        label: "Grant Types",
        items: {
            type: "string",
        },
        listRendering: {
            list: "all",
            load: async () => {
                return KNOWN_GRANT_TYPES;
            },
            compare(a: any, b: any) {
                const s1 = a as LocalGrantType;
                const s2 = b as LocalGrantType;

                if (s1.id === s2.id) {
                    return 0;
                } else {
                    return s1.id < s2.id ? -1 : 1;
                }
            },
            transformForEditing: (selectedItems: any[], iteratingLoadedItem: any) => {
                const selectionList = (selectedItems || []) as string[];
                const typeItem = iteratingLoadedItem as LocalGrantType;
                const checked = selectionList.includes(typeItem.id);

                return {
                    checked: checked,
                    label: typeItem.description,
                    value: typeItem.id,
                }
            }
        }
    },
    {
        title: "response_types",
        label: "Response Types",
        items: {
            type: "string",
        },
        listRendering: {
            list: "all",
            load: async () => {
                return ["code"];
            },
            compare(a: any, b: any) {
                const s1 = a as string;
                const s2 = b as string;

                if (s1 === s2) {
                    return 0;
                } else {
                    return s1 < s2 ? -1 : 1;
                }
            },
            transformForEditing: (selectedItems: any[], iteratingLoadedItem: any) => {
                const selectionList = (selectedItems || []) as string[];
                const iteratingId = iteratingLoadedItem as string;
                const checked = selectionList.includes(iteratingId);

                return {
                    checked: checked,
                    label: iteratingId,
                    value: iteratingId,
                }
            }
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
            load: async () => {
                return await http.sendAndMapAs<IAMScope[]>(
                    "get",
                    "/rest/scopes/",
                    {
                        handleError: response => {
                            if (response.status === 401) {
                                ejectToLoginScreen();
                            } else {
                                response.text().then(content => {
                                    throw new HttpError(response.status, content)
                                });
                            }
                        }
                    }
                );
            },
            transformForEditing: (selectedItems: any[], iteratingLoadedItem: any) => {
                const typedItem = iteratingLoadedItem as IAMScope;
                const selections = selectedItems || [];
                const checked = selections.includes(typedItem.name as string);

                const label = typedItem.description ? typedItem.description : typedItem.name;
                return {
                    checked: checked,
                    label: typedItem.fixed ? `${label} (fixed)` : label,
                    value: typedItem.name as string,
                };
            }
        }
    },
];

export const IAM_USER_SCHEMA: ResourceSchema[] = [
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
    },
    {
        title: "email",
        label: "E-mail Address",
        type: "string",
        required: true,
    },
    {
        title: "full_name",
        label: "Full Name",
        type: "string",
        required: true,
    },
    {
        title: "password",
        label: "Password",
        type: "string",
        required: true,
        sensitive: true,
        hidden: true,
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
            load: async () => {
                return await http.sendAndMapAs<IAMRole[]>(
                    "get",
                    "/rest/roles/",
                    {
                        handleError: response => {
                            if (response.status === 401) {
                                ejectToLoginScreen();
                            } else {
                                response.text().then(content => {
                                    throw new HttpError(response.status, content)
                                });
                            }
                        }
                    }
                );
            },
            transformForEditing: (selectedItems: any[], iteratingLoadedItem: any) => {
                const typedItem = iteratingLoadedItem as IAMRole;
                const selections = selectedItems || [];
                const checked = selections.includes(typedItem.name as string);
                return {
                    checked: checked,
                    label: typedItem.description ? typedItem.description : typedItem.name,
                    value: typedItem.name as string,
                };
            }
        }
    },
]