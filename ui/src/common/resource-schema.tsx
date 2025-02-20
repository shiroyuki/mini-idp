import {http} from "./http-client";
import {IAMRole} from "./models";
import {CSSProperties} from "react";
import classNames from "classnames";

type dataType = "string" | "integer" | "float" | "boolean" | "object";

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
    transformForReading: (item: ListTransformedOption) => any;
    transformForEditing: (fieldDataList: any[], loadedListItem: any) => ListTransformedOption;
};

/**
 * JSON Schema (custom)
 */
export type ResourceSchema = {
    ///// Standard JSON Schema /////
    title?: string;
    type?: dataType;
    required?: boolean;
    items?: ResourceSchema;
    ///// Custom properties /////
    label?: string;
    readOnly?: boolean;
    hidden?: boolean;
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

export const IAM_USER_SCHEMA: ResourceSchema[] = [
    {
        title: "id",
        label: "ID",
        required: true,
        readOnly: true,
        hidden: true,
        style: {
            fontFamily: "monospace",
        }
    },
    {
        title: "name",
        label: "Username",
        required: true,
        isReferenceKey: true,
    },
    {
        title: "email",
        label: "E-mail Address",
        required: true,
    },
    {
        title: "full_name",
        label: "Full Name",
        required: true,
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
                return await http.simpleSend<IAMRole[]>("get", "/rest/roles/");
            },
            transformForReading: (item: ListTransformedOption) => {
                return (
                    <span key={item.value} className={classNames(["foundation-tag", item.checked ? "selected" : "not-selected"])}>{item.label}</span>
                );
            },
            transformForEditing: (fieldDataList: any[], loadedListItem: any) => {
                const typedItem = loadedListItem as IAMRole;
                const assignedRoles = fieldDataList || [];
                const checked = assignedRoles.includes(typedItem.name as string);
                return {
                    checked: checked,
                    label: typedItem.description ? `${typedItem.name} - ${typedItem.description}` : typedItem.name,
                    value: typedItem.name as string,
                };
            }
        }
    },
]