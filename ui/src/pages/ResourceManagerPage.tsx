import UIFoundation from "../components/UIFoundation";
import {FC, ReactElement, useCallback, useEffect, useMemo, useState} from "react";
import {Navigation, UIFoundationHeader} from "../components/UIFoundationHeader";
import {http} from "../common/http-client";
import classNames from "classnames";
import {LinearLoadingAnimation} from "../components/loaders";
import {ListRenderingOptions, ListTransformedOption, ResourceSchema} from "../common/resource-schema";
import {Link, useParams} from "react-router-dom";
import {ResourceView, ResourceViewMode} from "../components/ResourceView";
import {IAMUserReadOnly} from "../common/models";

type ListPageProps = {
    title: string;
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
                                                       listPage
                                                   }: MainProps) => {
    const {id} = useParams();
    const waypoints: Navigation[] = [
        {label: "IAM"},
        {label: listPage.title, path: `${baseFrontendUri}`},
    ];

    let body: ReactElement;

    if (id) {
        waypoints.push({label: id});
        body = (
            <SoloResource
                id={id}
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
    id: string;
    baseBackendUri: string;
    schema: ResourceSchema[];
}

export const SoloResource = ({id, baseBackendUri, schema}: SoloProps) => {
    const [inFlight, setInFlight] = useState<boolean>(false);
    const [isDirty, setDirty] = useState(false);
    const [currentMode, setCurrentMode] = useState<ResourceViewMode | undefined>("reader");
    const [resource, setResource] = useState<any|undefined>(undefined);

    const loadResource = useCallback(() => {
        setInFlight(true);
        http.simpleSend<any>("get", `${baseBackendUri}/${id}`)
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
        if (!resource) {
            console.warn("Invalid state to update");
            return null;
        }

        const patch = schema.filter(field => !field.readOnly && !field.hidden)
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
            const data = await http.simpleSend<any>("put", `${baseBackendUri}/${resource.id}`, {json: patch});
            setResource(data);
            setDirty(false);
            setCurrentMode("reader");
            return data;
        } catch (error) {
            console.warn(`Encountered unexpected error: ${error}`);
            setCurrentMode("editor");
            return null;
        }
    }, [resource, schema, baseBackendUri]);

    const updateLocalCopy = useCallback((key: string, value: any) => {
        // @ts-ignore
        setResource(prevState => {
            let updated = {...prevState} as IAMUserReadOnly;
            // @ts-ignore
            updated[key] = value;
            return updated;
        })
        setDirty(true);
    }, [setResource, setDirty]);

    const cancelEditing = useCallback(() => {
        if (isDirty) {
            loadResource();
        }
    }, [loadResource, isDirty]);

    useEffect(() => {
        loadResource();
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

const ResourceList = ({baseBackendUri, baseFrontendUri, schema}: ListProps) => {
    const [inFlight, setInFlight] = useState<number>(0);
    const [cacheMap, setCacheMap] = useState<{ [key: string]: any } | undefined>(undefined);
    const [resourceList, setResourceList] = useState<any[] | undefined>(undefined);

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
        http.simpleSend<any[]>("get", `${baseBackendUri}/`)
            .then((data) => {
                setResourceList(data);
                setInFlight(prevState => prevState - 1);
            });
    }, []);

    if (resourceList === undefined || cacheMap === undefined || inFlight > 0) {
        return <LinearLoadingAnimation label={"Loading..."}/>;
    }

    return (
        <div className="data-table-container">
            <div className="data-table-navigator">
                <div className="data-table-counter">{resourceList?.length || 0}</div>
            </div>
            <table className={classNames(["data-table"])}>
                <thead>
                <tr>
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
                    resourceList.map(resource => (
                        <tr key={schema[0].title}>
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
                    ))
                }
                </tbody>
            </table>
        </div>
    );
}