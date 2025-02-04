import {LinearLoadingAnimation} from "./loaders";
import Icon from "./Icon";
import React, {ChangeEvent, useCallback, useEffect, useMemo, useState} from "react";
import styles from "./UserProfile.module.css";
import classNames from "classnames";
import {ResourceView, Schema} from "./ResourceView";
import {IAMRole, IAMUserReadOnly} from "../common/models";

export const UserProfile = ({id}: { id?: string }) => {
    const targetResourceId = id ?? null;
    const [isDirty, setDirty] = useState(false);
    const [targetResource, setTargetResource] = useState<IAMUserReadOnly | undefined | null>(undefined);

    const loadResource = useCallback(() => {
        fetch(
            targetResourceId === null ? '/rpc/iam/self/profile' : `/rest/users/${targetResourceId}`,
            {
                method: "get",
                headers: {
                    Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
                },
            }
        ).then(async (response) => {
            if (response.status === 200) {
                setTargetResource(await response.json());
            } else {
                // TODO Handle HTTP 401, 403, 404, 5XX.
                console.error(`No clean handling for this response:\n\nHTTP ${response.status}: ${await response.text()}`)
                setTargetResource(null);
            }
            setDirty(false)
        });
    }, []);

    const updateRemoteCopy = useCallback(() => {
        if (!targetResource) {
            console.warn("The resource is not loaded.");
            return;
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

        fetch(
            `/rest/users/${targetResource.id}`,
            {
                method: "put",
                headers: {
                    Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(patch),
            }
        ).then(async (response) => {
            if (response.status === 200) {
                setTargetResource(await response.json());
            } else {
                // TODO Handle HTTP 401, 403, 404, 5XX.
                console.error(`No clean handling for this response:\n\nHTTP ${response.status}: ${await response.text()}`)
                setTargetResource(null);
                throw new Error("Update failed");
            }
            setDirty(false)
        });
    }, [targetResource]);

    useEffect(() => {
        if (targetResource === undefined) {
            loadResource();
        }
    }, [id]);

    const resourceSchema: Schema[] = useMemo(() => {
        return [
            {
                title: "id",
                label: "ID",
                required: true,
                readOnly: true,
                hidden: true,
                style: {
                    fontFamily: "monospace",
                }
            },
            {
                title: "name",
                label: "Username",
                required: true,
            },
            {
                title: "email",
                label: "E-mail Address",
                required: true,
            },
            {
                title: "full_name",
                label: "Full Name",
                required: true,
            },
            {
                title: "roles",
                label: "Roles",
                required: true,
                items: {
                    type: "string",
                },
                listRendering: {
                    list: "all",
                    load: async () => {
                        const getRolesResponse = await fetch(
                            '/rest/roles/',
                            {
                                method: "get",
                                headers: {
                                    Accept: "application/json",
                                }
                            }
                        );
                        const fetchedRoles = await getRolesResponse.json() as IAMRole[];
                        return fetchedRoles;
                    },
                    transform: (item: any) => {
                        const typedItem = item as IAMRole;
                        const assignedRoles = targetResource?.roles || [];
                        const checked = assignedRoles.includes(typedItem.name as string);
                        return {
                            checked: checked,
                            label: typedItem.description ? `${typedItem.name} - ${typedItem.description}` : typedItem.name,
                            value: typedItem.name as string,
                        };
                    }
                }
            },
        ]
    }, [targetResource?.roles]);

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
                <h1 className={styles.profileHeader}>
                    {targetResourceId === null ? "Your Profile" : (targetResource.full_name || targetResource.name)}
                </h1>
                <ResourceView
                    initialMode={"reader"}
                    fields={resourceSchema}
                    data={targetResource}
                    onUpdate={updateLocalCopy}
                    onCancel={cancelEditing}
                    onSubmit={updateRemoteCopy}
                />
            </>
        );
    }
};