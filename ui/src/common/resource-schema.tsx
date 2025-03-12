import {http, HttpError} from "./http-client";
import {IAMRole} from "./models";
import {CSSProperties} from "react";
import {ejectToLoginScreen} from "./helpers";

type JsonSchemaDataType = "string" | "number" | "integer" | "float" | "boolean" | "object";

export type ListTransformedOption = {
    checked: boolean;
    label?: string;
    value: string;
};

export type ListRenderingOptions = {
    list: "selected-only" | "all"; // default: all
    load: () => Promise<any[]>;
    maxSelections?: number; // default: -1 (no limit)
    minSelections?: number; // default: 0 (optional) or 1 (required)
    compare?: (a: any, b: any) => -1 | 0 | 1;
    transformForEditing: (fieldDataList: any[], loadedListItem: any) => ListTransformedOption;
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
            transformForEditing: (fieldDataList: any[], loadedListItem: any) => {
                const typedItem = loadedListItem as IAMRole;
                const assignedRoles = fieldDataList || [];
                const checked = assignedRoles.includes(typedItem.name as string);
                return {
                    checked: checked,
                    label: typedItem.description ? typedItem.description : typedItem.name,
                    value: typedItem.name as string,
                };
            }
        }
    },
]