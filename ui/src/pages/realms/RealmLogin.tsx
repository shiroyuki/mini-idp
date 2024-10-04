import { FormEvent, useState } from "react"
import './RealmLogin.scss'
import LoginComponent from "../../components/LoginComponent";
import { useLoaderData } from "react-router-dom";

export default function RealmLogin() {
  const loadedData = useLoaderData() as { realmId: string };

  return (
    <div className="login-screen realm">
      <LoginComponent realmId={ loadedData.realmId } />
    </div>
  )
}