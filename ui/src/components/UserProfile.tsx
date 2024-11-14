import {LinearLoadingAnimation} from "./loaders";
import Icon from "./Icon";
import {ChangeEvent, useEffect, useState} from "react";
import styles from "./UserProfile.module.css";
import classNames from "classnames";
import EditableText from "./EditableText";
import {ResourceView} from "./ResourceView";

export interface IAMUserReadOnly {
    id: string | null;
    name: string
    email: string
    full_name: string | null;
    roles: string[];
}

export const UserProfile = ({id}: { id?: string }) => {
    const targetResourceId = id ?? null;
    const [targetResource, setTargetResource] = useState<IAMUserReadOnly | undefined | null>(undefined);
    const [rolesToRevoke, setRolesToRevoke] = useState<string[]>([]);
    const toggleRoleToRevoke = (roleId: string) => {
        if (rolesToRevoke.includes(roleId)) {
            setRolesToRevoke(prev => prev.filter(r => r !== roleId));
        } else {
            setRolesToRevoke(prev => [...prev, roleId].sort());
        }
    }

    useEffect(() => {
        if (targetResource === undefined) {
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
                    console.error(`PANDA: No clean handling for this response:\n\nHTTP ${response.status}: ${await response.text()}`)
                    setTargetResource(null);
                }
            });
        }
    }, [targetResourceId]);

    if (targetResource === undefined) {
        return <LinearLoadingAnimation
            label={targetResourceId === null ? "Loading your profile" : `Accessing User ${targetResourceId}`}/>;
    } else if (targetResource === null) {
        // TODO Handle HTTP 401, 403, 404, 5XX.
        return <LinearLoadingAnimation label={`Failed to load User ${targetResourceId}`}/>;
    } else {
        return (
            <>
                <h1 className={styles.profileHeader}>
                    {targetResourceId === null ? "Your Profile" : (targetResource.full_name || targetResource.name)}
                </h1>
                <ResourceView
                    fields={ [
                        {
                            title: "id",
                            label: "ID",
                            required: true,
                            readOnly: true,
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
                        },
                    ] }
                    data={ targetResource }
                />
                <hr/>
                <dl className={styles.profile}>
                    <dt className={classNames([styles.dt, styles.profileName])}>Username</dt>
                    <dd className={classNames([styles.dd, styles.profileName])}>{targetResource.name}</dd>
                    <dt className={classNames([styles.dt, styles.profileEmail])}>E-mail Address</dt>
                    <dd className={classNames([styles.dd, styles.profileEmail])}>{targetResource.email}</dd>
                    <dt className={classNames([styles.dt, styles.profileFullName])}>Full Name</dt>
                    <dd className={classNames([styles.dd, styles.profileFullName])}>{targetResource.full_name}</dd>
                    <dt className={classNames([styles.dt, styles.profileRoles])}>
                        Roles
                        {rolesToRevoke.length > 0
                            ? <button className={classNames(["destructive", styles.headlineButton, styles.removeRolesButton])}>
                                <Icon name="remove"
                                      classes={[classNames([styles.headlineButtonIcon, styles.removeRolesButtonIcon])]}/>
                                Revoke selected role{rolesToRevoke.length === 1 ? "" : "s"}
                            </button>
                            : <button className={classNames(["primary", styles.headlineButton, styles.addRoleButton])}>
                                <Icon name="add"
                                      classes={[classNames([styles.headlineButtonIcon, styles.addRoleButtonIcon])]}/>
                                Grant new role
                            </button>}
                    </dt>
                    <dd className={classNames([styles.dd, styles.profileRoles])}>
                        <ul className={styles.profileRoleList}>
                            {targetResource.roles.map(role =>
                                <li key={role} className={styles.profileRole}>
                                <input type="checkbox" onChange={() => toggleRoleToRevoke(role)}/>
                                    {role}
                                </li>
                            )}
                        </ul>
                    </dd>
                </dl>
            </>
        );
    }
};