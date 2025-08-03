import React, {useCallback, useEffect, useMemo, useState} from "react";
import {LinearLoadingAnimation} from "./loaders";
import {ListRenderingOptions, NormalizedItem, ResourceSchema} from "../common/json-schema-definitions";
import styles from "./ResourceView.module.css";
import classNames from "classnames";
import {VCheckbox} from "./VElements";
import {RecourceFieldDataBlock} from "./RecourceFieldDataBlock";
import Icon from "./Icon";

type FieldControlProps = {
    schema: ResourceSchema;
    data: any;
    onUpdate?: (key: string, value: any) => any;
};
type ListState = {
    inFlight: boolean;
    data?: any[];
}
export const ResourceFieldControl = ({schema, data, onUpdate}: FieldControlProps) => {
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
                                                <span><RecourceFieldDataBlock data={itemLabel}/></span>
                                            </li>
                                        );
                                    })
                            }
                        </ul>
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