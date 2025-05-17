import UIFoundation from "../components/UIFoundation";
import {FC, ReactElement, useCallback, useEffect, useMemo, useRef, useState} from "react";
import {Navigation, UIFoundationHeader} from "../components/UIFoundationHeader";
import {ClientOptions, http} from "../common/http-client";
import classNames from "classnames";
import {LinearLoadingAnimation} from "../components/loaders";
import {Link, useNavigate, useNavigation, useParams, useResolvedPath} from "react-router-dom";
import {DataBlock, ResourceView, ResourceViewMode} from "../components/ResourceView";
import {ejectToLoginScreen, ListCollection} from "../common/helpers";
import Icon from "../components/Icon";
import {VCheckbox} from "../components/VElements";
import styles from "./ResourceManagerPage.module.css"
import {ErrorFeedback, GenericModel} from "../common/definitions";
import {ListRenderingOptions, NormalizedItem, ResourceSchema} from "../common/json-schema-definitions";

export type PerResourcePermission = "list" | "read" | "write" | "delete";
export type PerResourcePermissionFetcher = (item: GenericModel) => PerResourcePermission[]

type ListPageProps = {
    title: string;
}

type MainProps = {
    baseBackendUri: string;
    baseFrontendUri: string;
    schema: ResourceSchema;
    listPage: ListPageProps;
    getPermissions: PerResourcePermissionFetcher;
}

export const ResourceManagerPage: FC<MainProps> = ({
                                                       baseBackendUri,
                                                       baseFrontendUri,
                                                       schema,
                                                       listPage,
                                                       getPermissions,
                                                   }: MainProps) => {
    const navigate = useNavigate();
    const {id} = useParams();
    const currentId = id;
    const forCreation = id === "new";
    const waypoints: Navigation[] = [
        {label: "IAM"},
        {label: listPage.title, path: `${baseFrontendUri}`},
    ];

    const handleNewResourceCreation = useCallback((data: GenericModel) => {
        navigate(`${baseFrontendUri}/`);
    }, [navigate, baseFrontendUri]);

    let body: ReactElement;

    if (forCreation) {
        waypoints.push({label: "New"});
        body = (
            <SoloResource
                baseBackendUri={baseBackendUri}
                schema={schema}
                onCreate={handleNewResourceCreation}
                returningUri={baseFrontendUri}
                getPermissions={getPermissions}
            />
        )
    } else if (currentId !== undefined) {
        waypoints.push({label: currentId});
        body = (
            <SoloResource
                id={currentId}
                baseBackendUri={baseBackendUri}
                schema={schema}
                getPermissions={getPermissions}
            />
        )
    } else {
        body = (
            <ResourceList
                baseBackendUri={baseBackendUri}
                baseFrontendUri={baseFrontendUri}
                schema={schema}
                getPermissions={getPermissions}
            />
        );
    }

    return (
        <UIFoundation>
            <UIFoundationHeader
                navigation={waypoints}
            />
            {body}
        </UIFoundation>
    );
}

type SoloProps = {
    id?: string,
    baseBackendUri: string,
    schema: ResourceSchema,
    returningUri?: string,
    onCreate?: (data: GenericModel) => void,
    getPermissions: PerResourcePermissionFetcher
}

const makeClientOptions = (additionals?: ClientOptions) => {
    return {
        handleError: response => {
            switch (response.status) {
                case 401:
                    ejectToLoginScreen();
                    break;
            }
        },
        ...(additionals || {}),
    } as ClientOptions
}

export const SoloResource = ({
                                 id,
                                 baseBackendUri,
                                 schema,
                                 returningUri,
                                 onCreate,
                                 getPermissions
                             }: SoloProps) => {
    const navigate = useNavigate();

    const [inFlight, setInFlight] = useState<boolean>(false);
    const [dirtyFields, setDirtyFields] = useState<string[]>([]);
    const [currentMode, setCurrentMode] = useState<ResourceViewMode | undefined>(id === undefined ? "creator" : "reader");
    const [resource, setResource] = useState<any | undefined>(undefined);
    const permissions = useMemo(
        () => resource === undefined ? [] : getPermissions(resource),
        [resource, getPermissions]
    );
    const isReadable = useMemo(() => permissions.includes("read"), [permissions]);
    const isWritable = useMemo(() => onCreate !== undefined || permissions.includes("write"), [permissions, onCreate]);

    const isResourceDirty = useCallback(() => dirtyFields.length > 0, [dirtyFields.length]);

    const loadResource = useCallback(() => {
        setInFlight(true);
        setResource(undefined);

        http.sendAndMapAs<any>(
            "get",
            `${baseBackendUri}/${id}`,
            makeClientOptions()
        )
            .then(
                (data) => {
                    setResource(data);
                    setDirtyFields([]);
                    setInFlight(false);
                },
                (err) => {
                    console.warn(`Encountered unexpected error: ${err}`);
                    setResource(null);
                    setDirtyFields([]);
                    setInFlight(false);
                }
            )
    }, [baseBackendUri, id]);

    const updateRemoteCopy = useCallback(async () => {
        if (id === undefined) {
            const data = await http.sendAndMapAs<GenericModel>("post", `${baseBackendUri}/`, makeClientOptions({json: resource}));
            if (onCreate && data) {
                onCreate(data as GenericModel);
            }
            return []
        } else {
            if (!resource) {
                return [{error: "not_found"}];
            }

            const patch = Object.entries(schema.properties as { [field: string]: ResourceSchema })
                .filter(([_, field]) => !field.readOnly && !field.hidden)
                .map(([fieldName, field]) => {
                    return {
                        op: "replace",
                        path: "/" + fieldName,
                        // @ts-ignore
                        value: resource[fieldName],
                    }
                });

            setCurrentMode("writing");

            try {
                const data = await http.sendAndMapAs<any>("put", `${baseBackendUri}/${resource.id}`, makeClientOptions({json: patch}));
                setResource(data);
                setDirtyFields([]);
                setCurrentMode("reader");
                return [];
            } catch (error) {
                console.warn(`Encountered unexpected error: ${error}`);
                setCurrentMode("editor");
                return [{error: "unexpected"}];
            }
        }
    }, [resource, baseBackendUri, id, onCreate, schema.properties]);

    const updateLocalCopy = useCallback((key: string, value: any) => {
        // @ts-ignore
        setResource(prevState => {
            let updated = {...prevState} as GenericModel;
            // @ts-ignore
            updated[key] = value;
            return updated;
        })
        setDirtyFields(prevState => {
            const newState: string[] = [...prevState];
            if (!newState.includes(key)) {
                newState.push(key);
            }
            return newState;
        });
    }, [setResource, setDirtyFields]);

    const cancelEditing = useCallback(() => {
        if (currentMode === "creator") {
            if (returningUri !== undefined) {
                navigate(returningUri);
            } else {
                throw new Error("The returning URI is not defined.");
            }
        }
        if (isResourceDirty()) {
            loadResource();
        }
    }, [loadResource, currentMode, returningUri, navigate, isResourceDirty]);

    useEffect(() => {
        if (id !== undefined) {
            loadResource();
        }
    }, [setResource]);

    if (inFlight) {
        return <LinearLoadingAnimation label={"Loading..."}/>;
    } else if (onCreate === undefined && !isReadable) {
        return <p>
            You don't have permission to read this resource.
        </p>
    } else {
        return (
            <ResourceView
                schema={schema}
                data={resource}
                style={{marginBottom: "24px"}}
                initialMode={currentMode}
                switchToMode={setCurrentMode}
                isDirty={isWritable ? isResourceDirty : undefined}
                onUpdate={isWritable ? updateLocalCopy : undefined}
                onCancel={isWritable ? cancelEditing : undefined}
                onSubmit={isWritable ? updateRemoteCopy : undefined}
            />
        );
    }
}

type FieldValueListProps = {
    allResources: any[];
    listRenderingOption: ListRenderingOptions;
    selectedItems: any[];
};

const FieldValueList = ({allResources, listRenderingOption, selectedItems}: FieldValueListProps) => {
    const minimalListSize = 5;
    const [minimal, setMinimal] = useState<boolean>(true);

    const filteredList = allResources
        .filter(loadedItem => loadedItem !== undefined && loadedItem !== null)
        .map(loadedItem => listRenderingOption.normalize(selectedItems, loadedItem) as NormalizedItem<any>)
        .filter(loadedItem => loadedItem.checked);
    const displayedList = minimal ? filteredList.slice(0, minimalListSize) : filteredList;

    // @ts-ignore
    const toggleDisplaySize = (e) => {
        e.preventDefault()
        e.stopPropagation()
        setMinimal(prev => !prev);
    }

    const showLess = useMemo(() => displayedList.length === filteredList.length, [displayedList, filteredList]);

    // TODO Handled structured data with DataBlock

    return (
        <>
            <ul data-count={filteredList.length} data-display-limit={minimalListSize}>
                {
                    displayedList
                        .map(item => (
                            <li key={item.value}
                                className={classNames([item.checked ? "selected" : "not-selected"])}>
                                {item.label ?? <DataBlock data={item.value}/>}
                            </li>
                        ))
                }
            </ul>
            {
                filteredList.length > minimalListSize &&
                (
                    <a onClick={toggleDisplaySize} className={styles.toggleLessMoreList}>
                        <span>{showLess ? "↑" : "↓"}</span>
                        <span>Show {showLess ? "less" : "more"}</span>
                    </a>
                )
            }
        </>
    );
}

type FieldValuePrimitiveProps = {
    baseFrontendUri: string;
    field: ResourceSchema;
    data: any;
};

const FieldValuePrimitive = ({baseFrontendUri, field, data}: FieldValuePrimitiveProps) => {
    const navigate = useNavigate();
    const href = field.isReferenceKey ? `#${baseFrontendUri}/${data}` : undefined;
    const handleClick = field.isReferenceKey
        ? ((data: any) => navigate(`${baseFrontendUri}/${data}`))
        : undefined;

    return (
        <DataBlock
            data={data}
            href={href}
            onClick={handleClick}
        />
    );
}

type ListProps = {
    baseBackendUri: string,
    baseFrontendUri: string,
    schema: ResourceSchema,
    getPermissions: PerResourcePermissionFetcher
}

type DataTableControllerMode = "navigator" | "deletion:init" | "deletion:in-progress";

const ResourceList = ({
                          baseBackendUri,
                          baseFrontendUri,
                          schema,
                          getPermissions,
                      }: ListProps) => {
    const navigate = useNavigate();
    const [inFlight, setInFlight] = useState<number>(0);
    const [dataTableControllerMode, setDataTableControllerMode] = useState<DataTableControllerMode>("navigator");
    const [cacheMap, setCacheMap] = useState<{ [key: string]: any }>({});
    const [resourceList, setResourceList] = useState<GenericModel[] | undefined>(undefined);
    const [selectionList, setSelectionList] = useState<GenericModel[]>([]);
    const primaryKeyList = Object.entries(schema.properties as { [field: string]: ResourceSchema })
        .filter(([_, field]) => field.isPrimaryKey)
        .map(([fieldName, _]) => fieldName)
    const selectionCollection = useMemo(
        () => new ListCollection(
            selectionList,
            (given, seeker) => {
                for (const pkFieldName of primaryKeyList) {
                    if (given[pkFieldName] < seeker[pkFieldName]) {
                        return -1;
                    } else if (given[pkFieldName] > seeker[pkFieldName]) {
                        return 1;
                    }

                    // NOTE: When it is equal, check the next field.
                }

                return 0;
            }
        ),
        [selectionList, primaryKeyList]
    );

    const loadCache = useCallback(() => {
        setCacheMap({});

        for (const [fieldName, field] of Object.entries(schema.properties as { [field: string]: ResourceSchema })) {
            if (field.items && field.listRendering) {
                const fieldListRendering = field.listRendering as ListRenderingOptions;
                setInFlight(prevState => prevState + 1);
                fieldListRendering.load()
                    .then(availableItems => {
                        const fieldKey = fieldName;
                        setCacheMap(prevState => {
                            let newState: { [key: string]: any } = {};
                            newState = {...prevState};
                            newState[fieldKey] = availableItems;
                            return newState;
                        })
                        setInFlight(prevState => prevState - 1);
                    })
            }
        }
    }, [schema.properties])

    const loadResources = useCallback(() => {
        setInFlight(prevState => prevState + 1);

        http.sendAndMapAs<any[]>(
            "get",
            `${baseBackendUri}/`,
            makeClientOptions()
        ).then((data) => {
            setResourceList(data);
            setInFlight(prevState => prevState - 1);
        });

        loadCache()
    }, [baseBackendUri, loadCache]);

    useEffect(() => {
        setResourceList([]);
        setCacheMap({});
        setSelectionList([]);
        loadResources();
    }, [schema, baseBackendUri]);

    const toggleSelection = useCallback(
        (target: GenericModel, checked: boolean) => {
            if (selectionCollection.contains(target)) {
                setSelectionList(selectionCollection.remove(target).toArray());
            } else {
                setSelectionList(selectionCollection.add(target).toArray());
            }
        },
        [selectionCollection]
    )

    const toggleAllSelections = useCallback(
        (value: any, checked: boolean) => {
            if (checked) {
                setSelectionList([
                    ...(resourceList || [])
                        .filter(resource => getPermissions(resource).includes("delete"))
                ]);
            } else {
                setSelectionList([]);
            }
        },
        [setSelectionList, resourceList, getPermissions]
    )

    const askUserForDeleteConfirmation = useCallback(
        // @ts-ignore
        (e) => {
            e.preventDefault();
            e.stopPropagation();
            setDataTableControllerMode("deletion:init");
        },
        [setDataTableControllerMode]
    );

    const renderField = useCallback((fieldName: string, field: ResourceSchema, resource: GenericModel) => {
        const fieldKey = fieldName;
        const fieldData = resource[fieldKey];
        const listRenderingOption = field.items && field.listRendering;
        const classNameList = classNames([`data-table-field-type-${field.items ? "list" : field.type}`]);

        if (listRenderingOption !== undefined && cacheMap[fieldKey] === undefined) {
            return <td className={classNameList}><LinearLoadingAnimation/></td>;
        } else {
            return (
                <>
                    <td className={classNameList}>{
                        listRenderingOption !== undefined
                            ? <FieldValueList allResources={cacheMap[fieldKey] as any[]}
                                              listRenderingOption={listRenderingOption}
                                              selectedItems={fieldData}/>
                            : <FieldValuePrimitive baseFrontendUri={baseFrontendUri}
                                                   field={field}
                                                   data={fieldData}/>
                    }</td>
                </>
            );
        }
    }, [cacheMap]);

    const renderObjectRow = useCallback((rowEntry: GenericModel) => {
        const selectable = getPermissions(rowEntry).includes("delete");
        return (
            <tr>
                <td className={classNames(["data-table-row-selector", selectable ? "selectable" : "non-selectable"])}>
                    {
                        selectable
                            ? (
                                <VCheckbox
                                    disabled={dataTableControllerMode !== "navigator"}
                                    checked={selectionCollection.contains(rowEntry)}
                                    value={rowEntry}
                                    onClick={toggleSelection}
                                    onKeyUp={toggleSelection}
                                />
                            )
                            : <Icon name={"fullscreen"}/>
                    }
                </td>
                {
                    Object.entries(schema.properties as { [field: string]: ResourceSchema })
                        .filter(([fieldName, field]) => !field.hidden)
                        .map(([fieldName, field]) => renderField(fieldName, field, rowEntry))
                }
            </tr>
        );
    }, [getPermissions, dataTableControllerMode, selectionCollection, toggleSelection, renderField, schema.properties]);

    const writableResourceCount = useMemo(
        () => resourceList === undefined
            ? 0
            : resourceList
                .filter(resource => getPermissions(resource).includes("delete"))
                .length,
        [resourceList, getPermissions]
    );

    if (resourceList === undefined || cacheMap === undefined || inFlight > 0) {
        return <LinearLoadingAnimation label={"Loading..."}/>;
    }

    return (
        <div className={classNames(["data-table-container", styles.localDataTable])}>
            {
                // Data Table Deleter
                dataTableControllerMode.startsWith("deletion:") && (
                    <div className="data-table-deleter">
                        {
                            dataTableControllerMode === "deletion:init" && (
                                <>
                                    <span className="data-table-delete-message">
                                        <Icon name={"warning"}/>
                                        Continue to delete the selection{selectionCollection.size() && "s"}?
                                    </span>
                                    <span className={"spacer"}></span>
                                    <button
                                        className={"data-table-delete-confirm destructive"}
                                        // @ts-ignore
                                        onClick={async (e) => {
                                            e.preventDefault();
                                            e.stopPropagation();

                                            setDataTableControllerMode("deletion:in-progress");

                                            for (const selection of selectionList) {
                                                await http.send(
                                                    "delete",
                                                    `${baseBackendUri}/${selection.id}`,
                                                    makeClientOptions()
                                                );
                                                // TODO Implement proper error handling.
                                            }

                                            setSelectionList([]);
                                            setDataTableControllerMode("navigator");
                                            loadResources();
                                        }}
                                    >
                                        Proceed
                                    </button>
                                    <button
                                        onClick={async (e) => {
                                            e.preventDefault();
                                            e.stopPropagation();
                                            setDataTableControllerMode("navigator");
                                        }}
                                    >
                                        Not now
                                    </button>
                                </>
                            )
                        }

                        {
                            dataTableControllerMode === "deletion:in-progress" && (
                                <>
                                    <LinearLoadingAnimation label={"Deleting..."}/>
                                </>
                            )
                        }
                    </div>
                )
            }

            {
                // Data Table Navigator
                dataTableControllerMode === "navigator" && (
                    <div className="data-table-navigator">
                        <div className="data-table-navigator-primary">
                            <a href={`#${baseFrontendUri}/new`} className={"btn"}>
                                <Icon name={"add"}/>
                                <span>Add</span>
                            </a>
                            {
                                !selectionCollection.isEmpty() && (
                                    <button
                                        className={"data-table-delete-initiator"}
                                        onClick={askUserForDeleteConfirmation}
                                    >
                                        <Icon name={"delete"}/>
                                        <span>Remove</span>
                                        <span className={"data-table-delete-counter"}>
                                            {selectionCollection.size()}
                                        </span>
                                    </button>
                                )
                            }
                        </div>
                        <div className="data-table-navigator-secondary"></div>
                    </div>
                )
            }

            {
                // Data Table View
            }
            <table className={classNames(["data-table"])}>
                {
                    // Data Table Header
                }
                <thead>
                <tr>
                    <th className={"data-table-row-selector"}>
                        <VCheckbox
                            disabled={dataTableControllerMode !== "navigator"}
                            checked={
                                selectionCollection.isEmpty()
                                    ? false
                                    : (
                                        selectionCollection.size() === writableResourceCount
                                            ? true
                                            : "indeterminate"
                                    )
                            }
                            onClick={toggleAllSelections}
                            onKeyUp={toggleAllSelections}
                        />
                    </th>
                    {
                        Object.entries(schema.properties as { [key: string]: ResourceSchema })
                            .filter(([_, field]) => !field.hidden)
                            .map(([fieldName, field]) => (
                                <th key={`th-${fieldName}`}>{field.label}</th>
                            ))
                    }
                </tr>
                </thead>
                {
                    // Data Table Body
                }
                <tbody>{resourceList.map(renderObjectRow)}</tbody>
            </table>
        </div>
    );
}