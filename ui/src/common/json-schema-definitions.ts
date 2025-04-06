import {Comparator, DataLoader, ErrorFeedback, GenericModel} from "./definitions";
import {CSSProperties} from "react";
import {Validator} from "./validation";

export type JsonSchemaDataType = "string" | "number" | "integer" | "float" | "boolean" | "object";
export type NormalizedItem<T> = {
    checked: boolean;
    label?: string;
    value: T;
};
export type ListItemNormalizer<LoadedItemType, KeyType> = (selectedItems: KeyType[], iteratingLoadedItem: LoadedItemType) => NormalizedItem<KeyType>;
export type ListRenderingOptions = {
    list: "selected-only" | "all"; // default: all
    load: DataLoader<any>;
    maxSelections?: number; // default: -1 (no limit)
    minSelections?: number; // default: 0 (optional) or 1 (required)
    compare?: Comparator<any>;
    normalize: ListItemNormalizer<any, any>;
};

/**
 * JSON Schema (custom)
 */
export type ResourceSchema = {
    ///// Standard JSON Schema /////
    title?: string;
    type?: JsonSchemaDataType;
    /**
     * When it is TRUE, this property is considered as mandatory and cannot be null, undefined, or empty (blank string only).
     */
    required?: boolean;
    items?: ResourceSchema;
    properties?: {[field: string]: ResourceSchema}; // FIXME This is technically a map, not a list.
    ///// Custom properties /////
    label?: string;
    readOnly?: boolean;
    hidden?: boolean;
    constrains?: Validator<any>[];
    default?: any;
    /**
     * The capability for auto-generation
     *
     * - full:pre = fully automated by the UI
     * - full:post = fully automated by the backend
     * - init:pre = pre-filled by the UI with the autoGenerate function or the default value (default)
     * - init:post = filled by the backend if not available
     * - UNDEFINED = no automation available
     */
    autoGenerationCapability?: "full:pre" | "full:post" | "init:pre" | "init:post";
    autoGenerate?: () => Promise<any>;
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