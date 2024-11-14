import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { createHashRouter, RouterProvider } from 'react-router-dom';
import {UserProfilePage} from "./pages/UserProfilePage";
import LoginComponent from "./components/LoginComponent";

const router = createHashRouter([
  {
    path: '/',
    element: <App />,
    errorElement: <><h1>Error</h1><p>Please contact admins for support.</p></>,
    children: [
      {
        path: 'login',
        element: <LoginComponent/>,
      },
      {
        path: '',
        element: <UserProfilePage />,
      }
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
