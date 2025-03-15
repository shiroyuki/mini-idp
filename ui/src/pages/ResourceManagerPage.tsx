import UIFoundation from "../components/UIFoundation";
import {FC, ReactElement, useCallback, useEffect, useMemo, useRef, useState} from "react";
import {Navigation, UIFoundationHeader} from "../components/UIFoundationHeader";
import {ClientOptions, http} from "../common/http-client";
import classNames from "classnames";
import {LinearLoadingAnimation} from "../components/loaders";
import {ListRenderingOptions, ListTransformedOption, ResourceSchema} from "../common/resource-schema";
import {Link, useNavigate, useParams} from "react-router-dom";
import {ResourceView, ResourceViewMode} from "../components/ResourceView";
import {ejectToLoginScreen, ListCollection} from "../common/helpers";
import Icon from "../components/Icon";
import {VCheckbox} from "../components/VElements";
import styles from "./ResourceManagerPage.module.css"
import {GenericModel} from "../common/definitions";

export type PerResourcePermission = "list" | "read" | "write" | "delete";
export type PerResourcePermissionFetcher = (item: GenericModel) => PerResourcePermission[]

type ListPageProps = {
    title: string;
}

type MainProps = {
    baseBackendUri: string;
    baseFrontendUri: string;
    schema: ResourceSchema[];
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
    schema: ResourceSchema[],
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
    const [isDirty, setDirty] = useState(false);
    const [currentMode, setCurrentMode] = useState<ResourceViewMode | undefined>(id === undefined ? "creator" : "reader");
    const [resource, setResource] = useState<any | undefined>(undefined);
    const permissions = useMemo(
        () => resource === undefined ? [] : getPermissions(resource),
        [resource, getPermissions]
    );
    const isReadable = useMemo(() => permissions.includes("read"), [permissions]);
    const isWritable = useMemo(() => onCreate !== undefined || permissions.includes("write"), [permissions, onCreate]);

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
                    setDirty(false);
                    setInFlight(false);
                },
                (err) => {
                    console.warn(`Encountered unexpected error: ${err}`);
                    setResource(null);
                    setDirty(false);
                    setInFlight(false);
                }
            )
    }, [baseBackendUri, id]);

    const updateRemoteCopy = useCallback(async () => {
        if (id === undefined) {
            const data = await http.sendAndMapAs<GenericModel>("post", `${baseBackendUri}/`, makeClientOptions({json: resource}));
            if (onCreate && data) {
                onCreate(data as GenericModel)
            }
        } else {
            if (!resource) {
                console.warn("Invalid state to update");
                return null;
            }

            const patch = schema
                .filter(field => !field.readOnly && !field.hidden)
                .map(field => {
                    return {
                        op: "replace",
                        path: "/" + field.title,
                        // @ts-ignore
                        value: resource[field.title],
                    }
                });

            setCurrentMode("writing");

            try {
                const data = await http.sendAndMapAs<any>("put", `${baseBackendUri}/${resource.id}`, makeClientOptions({json: patch}));
                setResource(data);
                setDirty(false);
                setCurrentMode("reader");
                return data;
            } catch (error) {
                console.warn(`Encountered unexpected error: ${error}`);
                setCurrentMode("editor");
                return null;
            }
        }
    }, [resource, schema, baseBackendUri, id, onCreate]);

    const updateLocalCopy = useCallback((key: string, value: any) => {
        // @ts-ignore
        setResource(prevState => {
            let updated = {...prevState} as GenericModel;
            // @ts-ignore
            updated[key] = value;
            return updated;
        })
        setDirty(true);
    }, [setResource, setDirty]);

    const cancelEditing = useCallback(() => {
        if (currentMode === "creator") {
            if (returningUri !== undefined) {
                navigate(returningUri);
            } else {
                throw new Error("The returning URI is not defined.");
            }
        }
        if (isDirty) {
            loadResource();
        }
    }, [loadResource, isDirty, currentMode, returningUri, navigate]);

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
                fields={schema}
                data={resource}
                initialMode={currentMode}
                isDirty={isWritable ? () => isDirty : undefined}
                onUpdate={isWritable ? updateLocalCopy : undefined}
                onCancel={isWritable ? cancelEditing : undefined}
                onSubmit={isWritable ? updateRemoteCopy : undefined}
            />
        );
    }
}

type ListProps = {
    baseBackendUri: string,
    baseFrontendUri: string,
    schema: ResourceSchema[],
    getPermissions: PerResourcePermissionFetcher
}

type DataTableControllerMode = "navigator" | "deletion:init" | "deletion:in-progress";

const ResourceList = ({
                          baseBackendUri,
                          baseFrontendUri,
                          schema,
                          getPermissions,
                      }: ListProps) => {
    const [inFlight, setInFlight] = useState<number>(0);
    const [dataTableControllerMode, setDataTableControllerMode] = useState<DataTableControllerMode>("navigator");
    const [cacheMap, setCacheMap] = useState<{ [key: string]: any }>({});
    const [resourceList, setResourceList] = useState<GenericModel[] | undefined>(undefined);
    const [selectionList, setSelectionList] = useState<GenericModel[]>([]);
    const primaryKeyList = schema
        .filter(field => field.isPrimaryKey)
        .map(field => field.title as string)
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

        for (const rawField of schema) {
            const field = rawField as ResourceSchema;
            if (field.items && field.listRendering) {
                const fieldListRendering = field.listRendering as ListRenderingOptions;
                setInFlight(prevState => prevState + 1);
                fieldListRendering.load()
                    .then(availableItems => {
                        const fieldKey = field.title as string;
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
    }, [schema])

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
    )

    const renderFieldValueAsList = useCallback((fieldKey: string, fieldData: any[], listRenderingOption: ListRenderingOptions) => {
        if (cacheMap[fieldKey] === undefined) {
            console.warn(`No cache map for ${fieldKey}`);
            return <LinearLoadingAnimation/>;
        } else {
            return <ul>
                {
                    (cacheMap[fieldKey] as any[])
                        .filter(loadedItem => loadedItem !== undefined && loadedItem !== null)
                        .map(loadedItem => listRenderingOption.normalize(fieldData, loadedItem) as ListTransformedOption)
                        .filter(loadedItem => loadedItem.checked)
                        .map(item => (
                            <li key={item.value}
                                className={classNames([item.checked ? "selected" : "not-selected"])}>
                                {item.label}
                            </li>
                        ))
                }
            </ul>;
        }
    }, [cacheMap]);

    const renderFieldValueAsPrimitive = useCallback((field: ResourceSchema, fieldData: any) => {
        let renderedValue: any;

        if (fieldData === undefined || fieldData === null) {
            return "";
        }

        switch (field.type) {
            case "boolean":
                renderedValue = fieldData ? "true" : "false";
                break;
            case "number":
            case "integer":
            case "float":
                renderedValue = fieldData;
                break;
            case "object":
                renderedValue = <span style={{whiteSpace: "pre-wrap"}}
                                      dangerouslySetInnerHTML={{__html: JSON.stringify(fieldData)}}/>
                break;
            default:
                renderedValue = fieldData;
                break;
        }

        if (field.isReferenceKey) {
            return <Link to={`${baseFrontendUri}/${fieldData}`}>{renderedValue}</Link>
        } else {
            return renderedValue;
        }
    }, [baseFrontendUri]);

    const renderField = useCallback((field: ResourceSchema, resource: GenericModel) => {
        const fieldKey = field.title as string;
        const fieldData = resource[fieldKey];
        const listRenderingOption = field.items && field.listRendering;

        return (
            <>
                <td className={classNames([`data-table-field-type-${field.items ? "list" : field.type}`])}>{
                    listRenderingOption !== undefined
                        ? renderFieldValueAsList(fieldKey, fieldData, listRenderingOption as ListRenderingOptions)
                        : renderFieldValueAsPrimitive(field, fieldData)
                }</td>
            </>
        );
    }, [renderFieldValueAsList, renderFieldValueAsPrimitive]);

    const renderResource = useCallback((resource: GenericModel) => {
        const selectable = getPermissions(resource).includes("delete");
        return (
            <tr key={schema[0].title}>
                <td className={classNames(["data-table-row-selector", selectable ? "selectable" : "non-selectable"])}>
                    {
                        selectable
                            ? (
                                <VCheckbox
                                    disabled={dataTableControllerMode !== "navigator"}
                                    checked={selectionCollection.contains(resource)}
                                    value={resource}
                                    onClick={toggleSelection}
                                    onKeyUp={toggleSelection}
                                />
                            )
                            : <Icon name={"fullscreen"}/>
                    }
                </td>
                {
                    schema.filter(field => !field.hidden)
                        .map(field => renderField(field, resource))
                }
            </tr>
        );
    }, [getPermissions, schema, dataTableControllerMode, selectionCollection, toggleSelection, renderField]);

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
                        schema.filter(field => !field.hidden)
                            .map(field => (
                                <th key={`th-${field.title}`}>{field.label}</th>
                            ))
                    }
                </tr>
                </thead>
                {
                    // Data Table Body
                }
                <tbody>{resourceList.map(renderResource)}</tbody>
            </table>
        </div>
    );
}