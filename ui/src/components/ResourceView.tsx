import styles from "./ResourceView.module.css";
import React, {CSSProperties, useCallback, useEffect, useState} from "react";
import {LinearLoadingAnimation} from "./loaders";
import classNames from "classnames";
import Icon from "./Icon";
import {FormError} from "../common/local-models";

type dataType = "string" | "integer" | "float" | "boolean" | "object";

type ListTransformedOption = {
    checked: boolean;
    label?: string;
    value: string;
};

type ListRenderingOptions = {
    list: "selected-only" | "all"; // default: all
    load: () => Promise<any[]>;
    maxSelections?: number; // default: -1 (no limit)
    minSelections?: number; // default: 0 (optional) or 1 (required)
    compare?: (a: any, b: any) => -1 | 0 | 1;
    transform: (item: any) => ListTransformedOption;
};

/**
 * JSON Schema (custom)
 */
export type Schema = {
    ///// Standard JSON Schema /////
    title?: string;
    type?: dataType;
    required?: boolean;
    items?: Schema;
    ///// Custom properties /////
    label?: string;
    readOnly?: boolean;
    hidden?: boolean;
    ///// For sensitive information, e.g. password /////
    requireRepeat?: boolean;
    sensitive?: boolean;
    ///// For rendering list /////
    listRendering?: ListRenderingOptions;
    ///// For minimal customization /////
    className?: string;
    style?: CSSProperties;
    ///// For custom rendering /////
    render?: (schema: Schema, data: any) => any;
};

type Data = {
    [k: string]: any,
};

type FieldInputProps = {
    schema: Schema;
    data: any;
    onUpdate?: (key: string, value: any) => any;
};

type ListState = {
    inFlight: boolean;
    data?: any[];
}

const FieldInput = ({schema, data, onUpdate}: FieldInputProps) => {
    if (schema.items) {
        if (!schema.listRendering) {
            throw new Error(`Field ${schema.title}: listRendering UNDEFINED`);
        }
    }

    if (schema.render) {
        return schema.render(schema, data);
    }

    const [listState, setListState] = useState<ListState | undefined>(undefined);

    const disabled = onUpdate === undefined || schema.readOnly || false;
    const isRenderingList = schema.items && schema.listRendering !== undefined;
    const fieldLabel = <label htmlFor={schema.title}>{schema.label || schema.title}</label>
    const props = {
        disabled: disabled,
        style: schema.style,
    };

    useEffect(() => {
        if (isRenderingList && listState === undefined) {
            setListState({
                inFlight: true,
                data: undefined,
            });

            schema.listRendering?.load()
                .then(items =>
                    setListState({
                        inFlight: false,
                        data: items,
                    })
                );
        }
    }, [schema, data, onUpdate]);

    const updateList = useCallback(
        (key: string, value: any, checked: boolean) => {
            if (!onUpdate) {
                return; // NOOP
            }

            if (checked) {
                data.push(value);
                onUpdate(schema.title as string, data);
            } else {
                const updatedData = (data as any[])
                    .filter(item => {
                        if (schema.listRendering?.compare) {
                            return schema.listRendering?.compare(item, value) !== 0;
                        } else {
                            return item !== value;
                        }
                    });
                onUpdate(schema.title as string, updatedData);
            }
        },
        [onUpdate, data, schema.title, schema.listRendering]
    );

    if (isRenderingList) {
        if (listState === undefined) {
            return <LinearLoadingAnimation label={"Please wait..."}/>;
        } else if (listState) {
            if (listState.inFlight) {
                return <LinearLoadingAnimation label={"Loading..."}/>;
            } else {
                const listRenderingOption = schema.listRendering as ListRenderingOptions;
                const listingClassNames = [styles.itemList];

                if (disabled) {
                    listingClassNames.push("read-only");
                }

                return (
                    <>
                        {fieldLabel}
                        <ul className={classNames([listingClassNames])}>
                            {
                                (listState.data as any[])
                                    .map(item => listRenderingOption.transform(item) as ListTransformedOption)
                                    .filter(item => {
                                        return (listRenderingOption.list === "selected-only" && item.checked)
                                            || (listRenderingOption.list === "all" && (!disabled || item.checked));
                                    })
                                    .map(item => {
                                        const itemLabel = item.label || item.value;

                                        return (
                                            <li key={item.value}>
                                                <input
                                                    type={"checkbox"}
                                                    disabled={disabled}
                                                    checked={item.checked}
                                                    onChange={ e => updateList(schema.title as string, item.value, e.target.checked ) }
                                                />
                                                <span>{itemLabel}</span>
                                            </li>
                                        );
                                    })
                            }
                        </ul>
                    </>
                );
            }

        }
    } else if (schema.type === "boolean") {
        return (
            <>
                <input
                    id={schema.title}
                    {...props}
                    type="checkbox"
                    checked={data || false}
                    onChange={(e) => {
                        if (onUpdate) {
                            onUpdate(schema.title as string, e.target.checked);
                        }
                    }}
                />
                {fieldLabel}
            </>
        );
    } else {
        return (
            <>
                {fieldLabel}
                <input
                    id={schema.title}
                    {...props}
                    type="text"
                    value={data}
                    onChange={(e) => {
                        if (onUpdate) {
                            onUpdate(schema.title as string, e.target.value);
                        }
                    }}
                />
            </>
        );
    }
}

type ResourceProp = {
    data?: Data;
    fields: Schema[];
    initialMode?: "reader" | "editor";
    onCancel?: () => void;
    onSubmit?: () => FormError[] | void;
    onUpdate?: (key: string, value: any) => any;
}

export const ResourceView = ({fields, data, initialMode, onUpdate, onCancel, onSubmit}: ResourceProp) => {
    const [mode, setMode] = React.useState<"reader" | "editor" | undefined>(initialMode || "reader");

    if (onUpdate && !onCancel) {
        console.warn("The event listener for cancelling the editor mode SHOULD be defined");
    }

    const handleFormSubmission = useCallback(
        () => {
            if (onSubmit) {
                const errors = onSubmit() || [];
                if (errors.length === 0) {
                    setMode("reader");
                    console.log("Foo");
                } else {
                    // TODO: Implement the form error feedback.
                }
            }
        },
        [onSubmit, setMode]
    );

    const abortEditing = useCallback(() => {
        if (confirm("Are you sure you want to discard all changes?")) {
            setMode("reader");
            if (onCancel) onCancel();
        }
    }, [onCancel, setMode]);

    return (
        <form className={styles.resourceForm} onSubmit={handleFormSubmission}>
            {
                onUpdate && (
                    <div className={styles.actions}>
                        {
                            mode === "reader"
                                ? (
                                    <>
                                        <button type={"button"} onClick={() => setMode("editor")}>Edit</button>
                                    </>
                                )
                                : (
                                    <>
                                        <button type={"reset"} onClick={abortEditing} title={"Cancel"}><Icon name={"arrow_back"}/></button>
                                    </>
                                )
                        }
                    </div>
                )
            }
            <div className={styles.controllers}>
                <div className={styles.controller}>
                    {
                        fields.filter(f => !f.hidden)
                            .map(f => (
                                <FieldInput
                                    key={f.title}
                                    schema={f}
                                    data={data !== undefined ? data[f.title as string] : undefined}
                                    onUpdate={mode === "editor" ? onUpdate : undefined}
                                />
                            ))
                    }
                </div>
            </div>
            {mode === "editor" && (
                <div className={styles.secondaryActions}>
                    <button type={"submit"}>{data ? "Save" : "Create"}</button>
                </div>
            )}
        </form>
    );
}