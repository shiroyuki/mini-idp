import styles from "./ResourceView.module.css";
import React, {CSSProperties, useCallback, useEffect, useMemo, useState} from "react";
import {LinearLoadingAnimation} from "./loaders";
import classNames from "classnames";
import Icon from "./Icon";
import {ErrorFeedback, GenericModel} from "../common/definitions";
import {VCheckbox} from "./VElements";
import {ListRenderingOptions, NormalizedItem, ResourceSchema} from "../common/json-schema-definitions";
import {FinalValidationResult, isFinalValidationResultOk} from "../common/validation";

type FieldInputProps = {
    schema: ResourceSchema;
    data: any;
    onUpdate?: (key: string, value: any) => any;
};

type ListState = {
    inFlight: boolean;
    data?: any[];
}

type DataBlockProps = {
    data: any;
    onClick?: (data: any) => void;
}

export const DataBlock = ({data, onClick}: DataBlockProps) => {
    if (data === undefined || data === null) {
        return <div className={"value-placeholder"}>null</div>;
    }

    // TODO Instead of guessing the data type, request for the schema.
    const dataType = typeof data;
    let renderedValue: any;

    // @ts-ignore
    const handleClickOnContent = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();

        if (onClick) {
            onClick(data);
        }
    }, [onClick]);

    if (dataType === "object") {
        // TODO Currently, this part only handles one level-depth object.
        return (
            <table className={styles.dataBlockObject}>
                <tbody>
                {
                    Object.keys(data)
                        .map((key: string) => {
                            return (
                                <tr key={key}>
                                    <th>{key}</th>
                                    <td><DataBlock data={data[key]} onClick={onClick}/></td>
                                </tr>
                            )
                        })
                }
                </tbody>
            </table>
        )
    } else {
        switch (dataType) {
            case "string":
            case "number":
                renderedValue = data;
                break;
            case "boolean":
                renderedValue = data ? "true" : "false";
                break;
            default:
                throw new Error(`Unknown data type of ${dataType}`);
        }

        if (onClick) {
            return (
                <a className={styles.dataBlockReferenceLink}
                   onClick={handleClickOnContent}>{renderedValue}</a>
            );
        } else {
            return renderedValue;
        }
    }
}

const FieldInput = ({schema, data, onUpdate}: FieldInputProps) => {
    const minimumShownItemLength = 3;
    const [minimal, setMinimal] = useState<boolean>(true);
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
    const [queryOnValue, setQueryOnValue] = useState<string>('');
    const patternQueryOnValue = useMemo<RegExp>(() => new RegExp(queryOnValue.trim(), 'imu'), [queryOnValue]);

    const disabled = onUpdate === undefined || schema.readOnly || false;
    const isRenderingList = schema.items && schema.listRendering !== undefined;
    const fieldLabelText = schema.label || schema.title;
    const fieldLabel = <label htmlFor={schema.title}>{fieldLabelText}</label>
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
        (_: string, value: any, checked: boolean) => {
            if (!onUpdate) {
                return; // NOOP
            }

            let updatedData = [...(data || [])];

            if (checked) {
                updatedData.push(value);
                onUpdate(schema.title as string, updatedData);
            } else {
                updatedData = updatedData
                    .filter(item => {
                        if (schema.listRendering?.compare) {
                            return schema.listRendering.compare(item, value) !== 0;
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

    // @ts-ignore
    const handleListMinimalism = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setMinimal(prev => !prev);
    }

    if (isRenderingList) {
        if (listState === undefined) {
            return <LinearLoadingAnimation label={"Please wait..."}/>;
        } else if (listState) {
            if (listState.inFlight) {
                return <LinearLoadingAnimation label={`Loading ${fieldLabelText}...`}/>;
            } else {
                const listRenderingOption = schema.listRendering as ListRenderingOptions;
                const listingClassNames = [styles.itemList];

                if (disabled) {
                    listingClassNames.push(styles.itemListReadOnly);
                }

                const listData = listState.data as any[];
                const filteredList = listData
                    .slice(0, minimal ? minimumShownItemLength : listData.length)
                    .map(item => listRenderingOption.normalize(data, item) as NormalizedItem<any>)
                    .filter(item => {
                        return (listRenderingOption.list === "selected-only" && item.checked)
                            || (listRenderingOption.list === "all" && (!disabled || item.checked));
                    })
                    .filter(item => (
                        queryOnValue.trim().length === 0 // Filter is not in used.
                        || item.value.match(patternQueryOnValue) // Search on the value.
                        || item.label?.match(patternQueryOnValue) // Search on the label.
                    ));

                return (
                    <div className={classNames([styles.controller])} data-type={"list"}>
                        {fieldLabel}
                        {
                            !disabled
                            && listData.length > 8
                            && <input
                                type={"text"}
                                className={styles.itemListFilter}
                                value={queryOnValue}
                                placeholder={`Type something here to filter "${fieldLabelText}"`}
                                onChange={e => setQueryOnValue(e.currentTarget.value)}
                            />
                        }
                        <ul className={classNames([listingClassNames])} data-count={filteredList.length}>
                            {
                                filteredList
                                    .map(item => {
                                        const itemLabel = item.label || item.value;

                                        return (
                                            <li key={item.value}>
                                                <VCheckbox
                                                    className={styles.itemListCheckbox}
                                                    checked={item.checked}
                                                    value={item.value}
                                                    disabled={disabled}
                                                    onChange={(value, nextChecked) => {
                                                        updateList(schema.title as string, value, nextChecked);
                                                    }}
                                                />
                                                <span><DataBlock data={itemLabel}/></span>
                                            </li>
                                        );
                                    })
                            }
                        </ul>
                        { listData.length > minimumShownItemLength ?? (
                            <button onClick={handleListMinimalism}>{minimal ? "Show more" : "Show less"}</button>
                        ) }
                    </div>
                );
            }

        }
    } else if (schema.type === "boolean") {
        return (
            <div className={classNames([styles.controller])} data-type={schema.type}>
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
            </div>
        );
    } else if (schema.sensitive) {
        return (
            <div className={classNames([styles.controller])} data-type={schema.type}>
                {fieldLabel}
                <div
                    className={classNames([styles.sensitiveInput, showSecret ? styles.secretRevealed : styles.secretHidden])}>
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
            </div>
        );
    } else {
        return (
            <div className={classNames([styles.controller])} data-type={schema.type}>
                {fieldLabel}
                <input
                    id={schema.title}
                    {...props}
                    type={"text"}
                    value={data}
                    onChange={handleUpdate}
                />
            </div>
        );
    }
}

export type ResourceViewMode = "read-only" | "reader" | "editor" | "writing" | "creator";

type ResourceProp = {
    data?: GenericModel;
    schema: ResourceSchema;
    style?: CSSProperties;
    initialMode?: ResourceViewMode;
    finalValidationResult?: FinalValidationResult | null; // If this is null or undefined, it is considered "valid".
    isDirty?: () => boolean;
    switchToMode: (mode: ResourceViewMode) => void;
    onCancel?: () => void;
    onSubmit?: () => Promise<ErrorFeedback[]>;
    onUpdate?: (key: string, value: any) => any;
}

export const ResourceView = ({
                                 schema,
                                 data,
                                 style,
                                 initialMode,
                                 finalValidationResult,
                                 isDirty,
                                 switchToMode,
                                 onUpdate,
                                 onCancel,
                                 onSubmit
                             }: ResourceProp) => {

    if (onUpdate && !onCancel) {
        console.warn("The event listener for cancelling the editor mode SHOULD be defined");
    }

    const submitFormData = useCallback(
        async () => {
            if (onSubmit) {
                switchToMode("writing");
                const errors: ErrorFeedback[] = (await onSubmit()) || [];
                if (errors.length === 0) {
                    switchToMode("reader");
                } else {
                    switchToMode("editor");
                    // TODO: Implement the form error feedback.
                    console.log(errors);
                }
            }
        },
        [onSubmit, switchToMode]
    )

    const handleFormSubmission = useCallback(
        // @ts-ignore
        async (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (isFinalValidationResultOk(finalValidationResult)) {
                console.log("A");
                await submitFormData();
            } else {
                console.warn("Form submission blocked due to", finalValidationResult);
            }
        },
        [submitFormData, finalValidationResult]
    );

    // @ts-ignore
    const startEditing = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        switchToMode("editor");
    }, [switchToMode]);

    const abortEditing = useCallback(() => {
        const cleanCancellation = isDirty && !isDirty();

        if (initialMode === "creator") {
            if (confirm("Are you sure you want to discard all changes?")) {
                if (onCancel) onCancel();
                else alert("The cancellation of creation is not implemented.");
            }
        } else {
            if (cleanCancellation || confirm("Are you sure you want to discard all changes?")) {
                switchToMode("reader");
                if (onCancel) onCancel();
            }
        }
    }, [onCancel, switchToMode, isDirty, initialMode]);

    const inWritingMode = initialMode === "editor" || initialMode === "creator";
    const showActions = (initialMode === "reader" || inWritingMode) && onUpdate !== undefined;
    const cancelLabel = (isDirty && isDirty()) ? "Discard changes" : "Stop editing";

    if (initialMode === "writing") {
        return <LinearLoadingAnimation label={"Please wait..."}/>;
    }

    return (
        <form className={styles.resourceForm} style={style} onSubmit={handleFormSubmission} autoComplete="off">
            <div className={styles.controllers}>
                {
                    Object.entries(schema.properties as { [key: string]: ResourceSchema })
                        .filter(([_, f]) => {
                            if (f.autoGenerationCapability === "full:post" || f.autoGenerationCapability === "full:pre") {
                                return false; // the fully generated field will not be editable.
                            } else if (initialMode === "creator") {
                                return true; // show all fields
                            } else return !f.hidden;
                        })
                        .map(([fn, f]) => (
                            <FieldInput
                                key={fn}
                                schema={f}
                                data={(data !== undefined && data !== null) ? data[fn] : undefined}
                                onUpdate={inWritingMode ? onUpdate : undefined}
                            />
                        ))
                }
            </div>
            {
                showActions && (
                    <div className={styles.actions}>
                        {
                            initialMode === "reader"
                                ? (
                                    <>
                                        <button type={"button"} onClick={startEditing}>Edit</button>
                                    </>
                                )
                                : (
                                    <>
                                        <button type={"submit"}>
                                            {initialMode === "editor" ? "Save" : "Create"}
                                        </button>
                                        <button type={"reset"}
                                                onClick={abortEditing}
                                                title={cancelLabel}>
                                            {initialMode === "editor" ? cancelLabel : "Cancel"}
                                        </button>
                                    </>
                                )
                        }
                    </div>
                )
            }
        </form>
    );
}