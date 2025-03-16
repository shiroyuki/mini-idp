import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import {createHashRouter, RouterProvider} from 'react-router-dom';
import LoginComponent from "./components/LoginComponent";
import UIFoundation from "./components/UIFoundation";
import {PerResourcePermission, PerResourcePermissionFetcher, ResourceManagerPage} from "./pages/ResourceManagerPage";
import {
    IAM_OAUTH_CLIENT_SCHEMA,
    IAM_POLICY_SCHEMA,
    IAM_ROLE_SCHEMA,
    IAM_SCOPE_SCHEMA,
    IAM_USER_SCHEMA
} from "./common/resource-schema";
import {FrontPage} from "./pages/FrontPage";
import {MyProfilePage} from "./pages/MyProfilePage";
import {IAMPolicy, IAMRole, IAMScope, IAMUser} from "./common/models";
import {storage} from "./common/storage";
import {getAccessToken} from "./common/token";
import {GenericModel} from "./common/definitions";

const convertScopesToPermissions = (scopePrefix: string): PerResourcePermission[] => {
    const token = getAccessToken();

    if (token === null) {
        return [];
    }

    const scopes = token.scopes;

    if (scopes.includes("idp.root") || scopes.includes("idp.admin")) {
        return ["delete", "list", "read", "write"];
    }

    return scopes
        .filter(scope => scope.startsWith(scopePrefix + "."))
        .map(scope => scope.substring(scopePrefix.length)) as PerResourcePermission[];
}

interface FixableResource extends GenericModel {
    fixed?: boolean | null;
}

function getPermissionsForFixableResource<T extends FixableResource>(scopePrefix: string, item: T): PerResourcePermission[] {
    const defaultPermissions = convertScopesToPermissions(scopePrefix);

    if (defaultPermissions.length === 0) {
        return [];
    } else if ((item as T).fixed) {
        return defaultPermissions.includes("read")
            ? ["read"]
            : [];
    } else {
        return defaultPermissions;
    }
}

const getPermissionPerPolicy: PerResourcePermissionFetcher = (item: GenericModel) => {
    return getPermissionsForFixableResource('idp.policy', item as IAMPolicy);
};

const getPermissionPerRole: PerResourcePermissionFetcher = (item: GenericModel) => {
    return getPermissionsForFixableResource('idp.role', item as IAMRole);
};

const getPermissionPerScope: PerResourcePermissionFetcher = (item: GenericModel) => {
    return getPermissionsForFixableResource('idp.scope', item as IAMScope);
};

const getPermissionPerClient: PerResourcePermissionFetcher = (item: GenericModel) => {
    return convertScopesToPermissions('idp.client');
};

const getPermissionPerUser: PerResourcePermissionFetcher = (item: GenericModel) => {
    const user = item as IAMUser;
    const token = getAccessToken();

    if (token === null) {
        return [];
    }

    const scopes = token.scopes;
    const claims = token.claims;
    const currentUserId = claims.sub;

    const permissions: PerResourcePermission[] = ["read"];

    if (scopes.includes("idp.root") || scopes.includes("idp.admin") || scopes.includes("idp.user.write")) {
        permissions.push("write");
    }

    if (![user.id, user.name].includes(currentUserId) /* TODO or the roles permit */) {
        permissions.push("delete");
    }

    return permissions;
}

function makeUserManagerPage() {
    return <ResourceManagerPage
        baseBackendUri={"/rest/users"}
        baseFrontendUri={"/users"}
        schema={IAM_USER_SCHEMA}
        listPage={
            {
                title: "Users",
            }
        }
        getPermissions={getPermissionPerUser}
    />;
}

function makeRoleManagerPage() {
    return <ResourceManagerPage
        baseBackendUri={"/rest/roles"}
        baseFrontendUri={"/roles"}
        schema={IAM_ROLE_SCHEMA}
        listPage={
            {
                title: "Roles",
            }
        }
        getPermissions={getPermissionPerRole}
    />;
}

function makeScopeManagerPage() {
    return <ResourceManagerPage
        baseBackendUri={"/rest/scopes"}
        baseFrontendUri={"/scopes"}
        schema={IAM_SCOPE_SCHEMA}
        listPage={
            {
                title: "Scopes",
            }
        }
        getPermissions={getPermissionPerScope}
    />;
}

function makeOAuthClientManagerPage() {
    return <ResourceManagerPage
        baseBackendUri={"/rest/clients"}
        baseFrontendUri={"/clients"}
        schema={IAM_OAUTH_CLIENT_SCHEMA}
        listPage={
            {
                title: "OAuth Clients",
            }
        }
        getPermissions={getPermissionPerClient}
    />
}

function makePolicyManagerPage() {
    return <ResourceManagerPage
        baseBackendUri={"/rest/policies"}
        baseFrontendUri={"/policies"}
        schema={IAM_POLICY_SCHEMA}
        listPage={
            {
                title: "Policies (Beta)",
            }
        }
        getPermissions={getPermissionPerPolicy}
    />
}

const router = createHashRouter([
    {
        path: '/',
        element: <App/>,
        errorElement: (
            <UIFoundation>
                <h1 style={{textTransform: "uppercase", fontSize: "2rem", paddingTop: "24px"}}>Not available</h1>
                <p style={{margin: "1rem 0"}}>
                    If you think this is our mistake, please file an issue on <a
                    href="https://github.com/shiroyuki/mini-idp/issues">GitHub</a>.
                </p>
            </UIFoundation>
        ),
        children: [
            {
                path: 'login',
                element: <LoginComponent/>,
            },
            {
                path: 'users',
                // @ts-ignore
                element: makeUserManagerPage(),
                children: [
                    {
                        path: ":id",
                        element: makeUserManagerPage(),

                    }
                ]
            },
            {
                path: 'roles',
                // @ts-ignore
                element: makeRoleManagerPage(),
                children: [
                    {
                        path: ":id",
                        element: makeRoleManagerPage(),
                    }
                ]
            },
            {
                path: 'scopes',
                // @ts-ignore
                element: makeScopeManagerPage(),
                children: [
                    {
                        path: ":id",
                        element: makeScopeManagerPage(),
                    }
                ]
            },
            {
                path: 'clients',
                // @ts-ignore
                element: makeOAuthClientManagerPage(),
                children: [
                    {
                        path: ":id",
                        element: makeOAuthClientManagerPage(),
                    }
                ]
            },
            {
                path: 'policies',
                // @ts-ignore
                element: makePolicyManagerPage(),
                children: [
                    {
                        path: ":id",
                        element: makePolicyManagerPage(),
                    }
                ]
            },
            {
                path: 'account/profile',
                // @ts-ignore
                element: <MyProfilePage/>,
            },
            {
                path: '',
                // @ts-ignore
                element: <FrontPage/>,
            },
        ]
    },
])

const root = ReactDOM.createRoot(
    document.getElementById('root') as HTMLElement
);

root.render(
    <React.StrictMode>
        <RouterProvider router={router}/>
    </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
