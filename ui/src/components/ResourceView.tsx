import styles from "./ResourceView.module.css";
import React, {useCallback, useEffect, useState} from "react";
import {LinearLoadingAnimation} from "./loaders";
import classNames from "classnames";
import {ListRenderingOptions, ListTransformedOption, ResourceSchema} from "../common/resource-schema";
import {GenericModel} from "../common/models";
import Icon from "./Icon";

type FieldInputProps = {
    schema: ResourceSchema;
    data: any;
    onUpdate?: (key: string, value: any) => any;
};

type ListState = {
    inFlight: boolean;
    data?: any[];
}

const FieldInput = ({schema, data, onUpdate}: FieldInputProps) => {
    const isSensitiveField = schema.sensitive;
    const [showSecret, setShowSecret] = useState<boolean>(!isSensitiveField);

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

            let updatedData = [...(data || [])];

            if (checked) {
                updatedData.push(value);
                console.log("PANDA: CHECKED", value)
                onUpdate(schema.title as string, updatedData);
            } else {
                updatedData = updatedData
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

    const handleUpdate = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (onUpdate) {
            onUpdate(schema.title as string, e.target.value);
        }
    }

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
                                    .map(item => listRenderingOption.transformForEditing(data, item) as ListTransformedOption)
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
                                                    onChange={e => updateList(schema.title as string, item.value, e.target.checked)}
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
    } else if (schema.sensitive) {
        return (
            <>
                {fieldLabel}
                <div className={classNames([styles.sensitiveInput, showSecret ? styles.secretRevealed : styles.secretHidden])}>
                    <input
                        id={schema.title}
                        {...props}
                        type={showSecret ? "text" : "password"}
                        value={data}
                        onChange={handleUpdate}
                        autoComplete="off"
                    />
                    <button onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setShowSecret(prevState => !prevState)
                    }}>
                        <Icon name={showSecret ? "visibility_off" : "visibility"}/>
                    </button>
                </div>
            </>
        );
    } else {
        return (
            <>
                {fieldLabel}
                <input
                    id={schema.title}
                    {...props}
                    type={"text"}
                    value={data}
                    onChange={handleUpdate}
                />
            </>
        );
    }
}

export type ResourceViewMode = "read-only" | "reader" | "editor" | "writing" | "creator";

type ResourceProp = {
    data?: GenericModel;
    fields: ResourceSchema[];
    initialMode?: ResourceViewMode;
    isDirty?: () => boolean;
    onCancel?: () => void;
    onSubmit?: () => Promise<any> | null;
    onUpdate?: (key: string, value: any) => any;
}

export const ResourceView = ({fields, data, initialMode, isDirty, onUpdate, onCancel, onSubmit}: ResourceProp) => {
    const [mode, setMode] = React.useState<ResourceViewMode | undefined>(initialMode || "reader");

    if (onUpdate && !onCancel) {
        console.warn("The event listener for cancelling the editor mode SHOULD be defined");
    }

    const handleFormSubmission = useCallback(
        async (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (onSubmit) {
                setMode("writing");
                const errors = (await onSubmit()) || [];
                if (errors.length === 0) {
                    setMode("reader");
                } else {
                    setMode("editor");
                    // TODO: Implement the form error feedback.
                }
            }
        },
        [onSubmit, setMode]
    );

    const startEditing = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setMode("editor");
    }, [setMode]);

    const abortEditing = useCallback(() => {
        const cleanCancellation = isDirty && !isDirty();

        if (mode === "creator") {
            if (confirm("Are you sure you want to discard all changes?")) {
                if (onCancel) onCancel();
                else alert("The cancellation of creation is not implemented.");
            }
        } else {
            if (cleanCancellation || confirm("Are you sure you want to discard all changes?")) {
                setMode("reader");
                if (onCancel) onCancel();
            }
        }
    }, [onCancel, setMode, isDirty, mode]);

    const inWritingMode = mode === "editor" || mode === "creator";
    const showActions = (mode === "reader" || inWritingMode) && onUpdate !== undefined;
    const cancelLabel = (isDirty && isDirty()) ? "Discard changes" : "Stop editing";

    if (mode === "writing") {
        return <LinearLoadingAnimation label={"Please wait..."}/>;
    }

    return (
        <form className={styles.resourceForm} onSubmit={handleFormSubmission} autoComplete="off">
            <div className={styles.controllers}>
                {
                    fields
                        .filter(f => {
                            if (f.autoGenerationCapability === "full:post" || f.autoGenerationCapability === "full:pre") {
                                return false; // the fully generated field will not be editable.
                            } else if (mode === "creator") {
                                return true; // show all fields
                            } else if (f.hidden) {
                                return false;
                            } else {
                                return true;
                            }
                        })
                        .map(f => (
                            <div className={styles.controller}>
                                <FieldInput
                                    key={f.title}
                                    schema={f}
                                    data={(data !== undefined && data !== null) ? data[f.title as string] : undefined}
                                    onUpdate={inWritingMode ? onUpdate : undefined}
                                />
                            </div>
                        ))
                }
            </div>
            {
                showActions && (
                    <div className={styles.actions}>
                        {
                            mode === "reader"
                                ? (
                                    <>
                                        <button type={"button"} onClick={startEditing}>Edit</button>
                                    </>
                                )
                                : (
                                    <>
                                        <button type={"submit"}>{mode === "editor" ? "Save" : "Create"}</button>
                                        {data && <button type={"reset"} onClick={abortEditing}
                                                         title={cancelLabel}>{cancelLabel}</button>}
                                    </>
                                )
                        }
                    </div>
                )
            }
        </form>
    );
}