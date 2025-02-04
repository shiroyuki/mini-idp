import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import {createHashRouter, RouterProvider} from 'react-router-dom';
import {UserProfilePage} from "./pages/UserProfilePage";
import LoginComponent from "./components/LoginComponent";
import {UserListPage} from './pages/UserListPage';
import UIFoundation from "./components/UIFoundation";
import {ResourceManagerPage} from "./pages/ResourceManagerPage";

const router = createHashRouter([
    {
        path: '/',
        element: <App/>,
        errorElement: (
            <UIFoundation>
                <h1 style={{textTransform: "uppercase", fontSize: "2rem"}}>Not available</h1>
                <p style={{margin: "1rem 0"}}>
                    The user interface you have requested is sadly <b>unavailable</b>.
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
                element: <ResourceManagerPage baseUrl={ "/rest/users" } listPage={ {title: "Users"} }/>,
            },
            {
                path: '',
                // @ts-ignore
                element: <UserProfilePage/>,
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
