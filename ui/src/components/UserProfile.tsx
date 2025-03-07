import {LinearLoadingAnimation} from "./loaders";
import React, {useCallback, useEffect, useState} from "react";
import {ResourceView, ResourceViewMode} from "./ResourceView";
import {IAMRole, IAMUserReadOnly} from "../common/models";
import {UIFoundationHeader} from "./UIFoundationHeader";
import {http} from "../common/http-client";
import {IAM_USER_SCHEMA} from "../common/resource-schema";

export const UserProfile = ({id, mode}: { id?: string, mode?: ResourceViewMode }) => {
    const targetResourceId = id ?? null;
    const [isDirty, setDirty] = useState(false);
    const [currentMode, setCurrentMode] = useState<ResourceViewMode | undefined>(mode || "reader");
    const [targetResource, setTargetResource] = useState<IAMUserReadOnly | undefined | null>(undefined);
    const resourceSchema = IAM_USER_SCHEMA;

    const loadResource = useCallback(() => {
        http.sendAndMapAs<IAMUserReadOnly>("get", targetResourceId === null ? '/rpc/iam/self/profile' : `/rest/users/${targetResourceId}`)
            .then(
                (data) => {
                    setTargetResource(data);
                    setDirty(false)
                },
                (err) => {
                    console.warn(`Encountered unexpected error: ${err}`);
                    setTargetResource(null);
                    setDirty(false)
                }
            )
    }, []);

    const updateRemoteCopy = useCallback(async () => {
        if (!targetResource) {
            console.warn("Invalid state to update");
            return null;
        }

        const patch = resourceSchema.filter(field => !field.readOnly && !field.hidden)
            .map(field => {
                return {
                    op: "replace",
                    path: "/" + field.title,
                    // @ts-ignore
                    value: targetResource[field.title],
                }
            });

        setCurrentMode("writing")

        try {
            const data = await http.sendAndMapAs<IAMUserReadOnly>("put", `/rest/users/${targetResource.id}`, {json: patch});
            setTargetResource(data);
            setDirty(false);
            setCurrentMode("reader");
            return data;
        } catch (error) {
            console.warn(`Encountered unexpected error: ${error}`);
            setCurrentMode("editor");
            return null;
        }
    }, [targetResource, resourceSchema]);

    useEffect(() => {
        if (targetResource === undefined) {
            loadResource();
        }
    }, [id]);

    const updateLocalCopy = useCallback((key: string, value: any) => {
        setTargetResource(prevState => {
            let updated = {...prevState} as IAMUserReadOnly;
            // @ts-ignore
            updated[key] = value;
            return updated;
        })
        setDirty(true);
    }, [setTargetResource, setDirty]);

    const cancelEditing = useCallback(() => {
        if (isDirty) {
            loadResource();
        }
    }, [loadResource, isDirty]);

    const isResourceDirty = useCallback(() => isDirty, [isDirty]);

    if (targetResource === undefined) {
        return <LinearLoadingAnimation
            label={targetResourceId === null ? "Loading your profile" : `Accessing User ${targetResourceId}`}
        />;
    } else if (targetResource === null) {
        // TODO Handle HTTP 401, 403, 404, 5XX.
        return <LinearLoadingAnimation
            label={targetResourceId === null ? "Failed to load your profile" : `Failed to load User ${targetResourceId}`}
        />;
    } else {
        return (
            <>
                <UIFoundationHeader
                    navigation={[{label: targetResourceId === null ? "Your Profile" : (targetResource.full_name || targetResource.name)}]}
                />
                <ResourceView
                    initialMode={currentMode}
                    fields={resourceSchema}
                    data={targetResource}
                    isDirty={isResourceDirty}
                    onUpdate={updateLocalCopy}
                    onCancel={cancelEditing}
                    onSubmit={updateRemoteCopy}
                />
            </>
        );
    }
};