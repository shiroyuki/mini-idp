import {http, HttpError} from "./http-client";
import {IAMRole, IAMScope} from "./models";
import {CSSProperties} from "react";
import {ejectToLoginScreen} from "./helpers";
import {Comparator, DataLoader, GenericModel} from "./definitions";

type JsonSchemaDataType = "string" | "number" | "integer" | "float" | "boolean" | "object";

export type ListTransformedOption<T> = {
    checked: boolean;
    label?: string;
    value: T;
};

export type ListItemNormalizer<LoadedItemType extends GenericModel, KeyType> = (selectedItems: KeyType[], iteratingLoadedItem: LoadedItemType) => ListTransformedOption<KeyType>;

export type ListRenderingOptions = {
    list: "selected-only" | "all"; // default: all
    load: DataLoader<any>;
    maxSelections?: number; // default: -1 (no limit)
    minSelections?: number; // default: 0 (optional) or 1 (required)
    compare?: Comparator<any>;
    normalize: ListItemNormalizer<any, any>;
};

function listItemsFrom<T>(listUrl: string): DataLoader<T> {
    return async () => {
        return await http.sendAndMapAs<T[]>(
            "get",
            listUrl,
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
    }
}

function listFixedItems(fixtures: any[]) {
    return () => new Promise<any[]>((resolve, _) => {resolve(fixtures)});
}

function normalizeItemWith<LoadedItemType extends GenericModel, KeyType>(valueField: string, labelField: string) {
    return (selectedItems: KeyType[], iteratingLoadedItem: LoadedItemType) => {
        const typedItem = iteratingLoadedItem as LoadedItemType;
        const selections = selectedItems || [];
        const value = typedItem[valueField] as KeyType;
        const label = typedItem[labelField] ?? value;
        const checked = selections.includes(value);

        return {
            checked: checked,
            label: label,
            value: value,
        };
    }
}

function normalizePrimitiveValue() {
    return (selectedItems: any[], iteratingLoadedItem: any) => {
        const selectionList = (selectedItems || []) as any[];
        const iteratingId = iteratingLoadedItem as any;
        const checked = selectionList.includes(iteratingId);

        return {
            checked: checked,
            label: iteratingId,
            value: iteratingId,
        }
    }
}

function compareItemsWith<T extends GenericModel>(valueField: string): Comparator<T> {
    return (a: T, b: T) => {
        if (a[valueField] === b[valueField]) {
            return 0;
        } else {
            return a[valueField] < b[valueField] ? -1 : 1;
        }
    }
}

function comparePrimitiveValues() {
    return (a: any, b: any) => {
        if (a === b) {
            return 0;
        } else {
            return a < b ? -1 : 1;
        }
    }
}

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
            load: listFixedItems(KNOWN_GRANT_TYPES),
            compare: compareItemsWith("id"),
            normalize: normalizeItemWith<LocalGrantType, string>("id", "description"),
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
            load: listFixedItems(["code"]),
            compare: comparePrimitiveValues(),
            normalize: normalizePrimitiveValue(),
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
            normalize: normalizeItemWith<IAMScope, string>("name", "description"),
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
            load: listItemsFrom<IAMRole>("/rest/roles/"),
            normalize: normalizeItemWith<IAMRole, string>("name", "description"),
        }
    },
]