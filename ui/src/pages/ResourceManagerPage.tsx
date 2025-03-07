import UIFoundation from "../components/UIFoundation";
import {FC, ReactElement, useCallback, useEffect, useMemo, useState} from "react";
import {Navigation, UIFoundationHeader} from "../components/UIFoundationHeader";
import {ClientOptions, http} from "../common/http-client";
import classNames from "classnames";
import {LinearLoadingAnimation} from "../components/loaders";
import {ListRenderingOptions, ListTransformedOption, ResourceSchema} from "../common/resource-schema";
import {Link, useNavigate, useParams} from "react-router-dom";
import {ResourceView, ResourceViewMode} from "../components/ResourceView";
import {GenericModel, IAMUserReadOnly} from "../common/models";
import {ejectToLoginScreen, ListCollection} from "../common/helpers";
import Icon from "../components/Icon";
import {VCheckbox} from "../components/VElements";

export type ItemMatcher = (given: any, seaker: any) => boolean;

type ListPageProps = {
    title: string;
    matchItem?: ItemMatcher;
}

type MainProps = {
    baseBackendUri: string;
    baseFrontendUri: string;
    schema: ResourceSchema[];
    listPage: ListPageProps;
}

export const ResourceManagerPage: FC<MainProps> = ({
                                                       baseBackendUri,
                                                       baseFrontendUri,
                                                       schema,
                                                       listPage,
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
        const referenceKeys = schema
            .filter(field => field.isReferenceKey)
            .map(field => data[field.title as string]);

        const primaryKeys = schema
            .filter(field => field.isPrimaryKey)
            .map(field => data[field.title as string]);

        if (referenceKeys.length > 0) {
            navigate(`${baseFrontendUri}/${referenceKeys[0]}`);
        } else if (primaryKeys.length > 0) {
            navigate(`${baseFrontendUri}/${primaryKeys[0]}`);
        } else {
            // TODO handle error/misconfiguration
        }
    }, [schema, navigate, baseFrontendUri]);

    let body: ReactElement;

    if (forCreation) {
        waypoints.push({label: "New"});
        body = (
            <SoloResource
                baseBackendUri={baseBackendUri}
                schema={schema}
                onCreate={handleNewResourceCreation}
                returningUri={baseFrontendUri}
            />
        )
    } else if (currentId !== undefined) {
        waypoints.push({label: currentId});
        body = (
            <SoloResource
                id={currentId}
                baseBackendUri={baseBackendUri}
                schema={schema}
            />
        )
    } else {
        body = (
            <ResourceList
                baseBackendUri={baseBackendUri}
                baseFrontendUri={baseFrontendUri}
                schema={schema}
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
    id?: string;
    baseBackendUri: string;
    schema: ResourceSchema[];
    returningUri?: string;
    onCreate?: (data: GenericModel) => void;
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

export const SoloResource = ({id, baseBackendUri, schema, returningUri, onCreate}: SoloProps) => {
    if (id === undefined && onCreate === undefined) {
        throw new Error("Either specify the ID (for accessing an existing resource) or define onCreate (for creating a new resource)");
    }

    const navigate = useNavigate();

    const [inFlight, setInFlight] = useState<boolean>(false);
    const [isDirty, setDirty] = useState(false);
    const [currentMode, setCurrentMode] = useState<ResourceViewMode | undefined>(id === undefined ? "creator" : "reader");
    const [resource, setResource] = useState<any | undefined>(undefined);

    const loadResource = useCallback(() => {
        setInFlight(true);

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
    } else {
        return (
            <ResourceView
                fields={schema}
                data={resource}
                initialMode={currentMode}
                isDirty={() => isDirty}
                onUpdate={updateLocalCopy}
                onCancel={cancelEditing}
                onSubmit={updateRemoteCopy}
            />
        );
    }
}

type ListProps = {
    baseBackendUri: string;
    baseFrontendUri: string;
    schema: ResourceSchema[];
}

const makeSelectionKey = (primaryKeyList: string[], data: GenericModel) => {
    const keyList = primaryKeyList.map(k => `${k}=${JSON.stringify(data[k])}`);
    return keyList.join(";");
}

const ResourceList = ({baseBackendUri, baseFrontendUri, schema}: ListProps) => {
    const [inFlight, setInFlight] = useState<number>(0);
    const [cacheMap, setCacheMap] = useState<{ [key: string]: any } | undefined>(undefined);
    const [resourceList, setResourceList] = useState<any[] | undefined>(undefined);
    const [selectionKeyList, setSelectionKeyList] = useState<string[]>([]);
    const [selectionList, setSelectionList] = useState<any[]>([]);
    const primaryKeyList = schema
        .filter(field => field.isPrimaryKey)
        .map(field => field.title as string)

    useEffect(() => {
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

        setInFlight(prevState => prevState + 1);
        http.sendAndMapAs<any[]>(
            "get",
            `${baseBackendUri}/`,
            makeClientOptions()
        )
            .then((data) => {
                setResourceList(data);
                setInFlight(prevState => prevState - 1);
            });
    }, []);

    const toggleSelection = (targetKey: string, checked: boolean) => {
        // const collection = new ListCollection(selectionList);
        // if (collection)

        if (selectionKeyList.includes(targetKey)) {
            setSelectionKeyList(previousSelectionKeyList => previousSelectionKeyList.filter(selectedKey => {
                return selectedKey !== targetKey;
            }));
        } else {
            setSelectionKeyList(previousSelectionKeyList => [...previousSelectionKeyList, targetKey]);
        }
    }

    const deleteResources = () => {
        ///
    }

    if (resourceList === undefined || cacheMap === undefined || inFlight > 0) {
        return <LinearLoadingAnimation label={"Loading..."}/>;
    }

    return (
        <div className="data-table-container">
            <div className="data-table-navigator">
                <div className="data-table-navigator-primary">
                    <a href={`#${baseFrontendUri}/new`} className={"btn"}><Icon name={"add"}/> Add</a>
                    {
                        selectionKeyList.length > 0 && (
                            <button className={"destructive"}><Icon name={"delete"}/> Remove</button>
                        )
                    }
                </div>
                <div className="data-table-navigator-secondary"></div>
            </div>
            <table className={classNames(["data-table"])}>
                <thead>
                <tr>
                    <th className={"data-table-row-selector"}></th>
                    {
                        schema.filter(field => !field.hidden)
                            .map(field => (
                                <th key={`th-${field.title}`}>{field.label}</th>
                            ))
                    }
                </tr>
                </thead>
                <tbody>
                {
                    resourceList.map(resource => {
                            const selectionKey = makeSelectionKey(primaryKeyList, resource)
                            return (
                                <tr key={schema[0].title}>
                                    <td className={"data-table-row-selector"}>
                                        <VCheckbox
                                            checked={selectionKeyList.includes(selectionKey)}
                                            value={selectionKey}
                                            onClick={toggleSelection}
                                            onKeyUp={toggleSelection}
                                        />
                                    </td>
                                    {
                                        schema.filter(field => !field.hidden)
                                            .map(field => {
                                                const fieldKey = field.title as string;
                                                const fieldData = resource[fieldKey];
                                                const listRenderingOption = field.items && field.listRendering;
                                                return (
                                                    <>
                                                        <td className={classNames([`data-table-field-type-${field.type}`])}>{
                                                            listRenderingOption !== undefined
                                                                ? (cacheMap[fieldKey] as any[])
                                                                    .map(loadedItem => listRenderingOption.transformForEditing(fieldData, loadedItem) as ListTransformedOption)
                                                                    .filter(loadedItem => loadedItem.checked)
                                                                    .map(loadedItem => listRenderingOption.transformForReading(loadedItem))
                                                                : (
                                                                    field.isReferenceKey
                                                                        ? <Link
                                                                            to={`${baseFrontendUri}/${fieldData}`}>{fieldData}</Link>
                                                                        : fieldData
                                                                )
                                                        }</td>
                                                    </>
                                                );
                                            })
                                    }
                                </tr>
                            )
                        }
                    )
                }
                </tbody>
            </table>
        </div>
    );
}