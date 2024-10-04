import { FormEvent, useState } from "react"
import './LoginComponent.scss';
import Icon from "./Icon";

interface LoginComponentProps {
  // TODO This is temporary. Will replace with "realm".
  realmId?: string | null;
}

interface Feedback {
  type: string;
  message?: string | null;
}

interface LoginComponentState {
  inFlight: boolean;
  feedback: Feedback | null;
}

interface Principle {
  id: string
  realm_id: string | null
  name: string
  email: string
  full_name: string | null
  roles: string[]
}

interface AuthenticationResponse {
  error?: string | null;
  error_description?: string | null;
  session_id: string | null;
  principle?: Principle | null;
  already_exists: boolean;
}

const LoginComponent: React.FC<LoginComponentProps> = ({ realmId }) => {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [componentState, setComponentState] = useState<LoginComponentState>({
    inFlight: false,
    feedback: null,
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;

    setFormData((prevData) => ({
      ...prevData,
      [name]: value
    }));
  };

  const initiateLogin = async (e: FormEvent) => {
    e.preventDefault();
    e.stopPropagation();

    setComponentState(prevData => ({
      ...prevData,
      inFlight: true,
      feedback: null,
    }));

    const postData = new FormData();
    postData.append('password', formData.password);
    postData.append('username', formData.username);

    const response = await fetch(
      `/realms/${realmId}/login`,
      {
        method: 'post',
        headers: { 'Accept': 'application/json' },
        body: postData,
      }
    );

    const responseBody = await response.text();

    if (response.status === 200) {
      const result: AuthenticationResponse = JSON.parse(responseBody);
      const resultOk: boolean = result.error === null;

      setComponentState(prevData => ({
        ...prevData,
        inFlight: false,
        // Temporary Measure... Require redirection
        feedback: {
          type: resultOk ? 'ok' : 'error',
          message: resultOk ? result.principle?.email : result.error,
        },
      }));
    } else {
      setComponentState(prevData => ({
        ...prevData,
        inFlight: false,
        feedback: {
          type: 'error',
          message: `HTTP ${response.status} : ${responseBody}`,
        },
      }));
    }
  };

  const feedback = componentState.feedback
    ? <div className={['feedback', 'feedback-of-' + componentState.feedback.type].join(' ')}>{componentState.feedback.message}</div>
    : null;

  const loginForm = (
    <form method="post" action="#" onSubmit={initiateLogin} >
      <div className="field">
        <label htmlFor="username">Username or Email Address</label>
        <input
          type="text"
          id="username"
          name="username"
          required
          value={formData.username}
          onChange={handleChange} />
      </div>

      <div className="field">
        <label htmlFor="password">Password</label>
        <input
          type="password"
          id="password"
          name="password"
          required
          value={formData.password}
          onChange={handleChange} />
      </div>

      <div className="actions">
        <button type="submit">Sign in</button>
      </div>
    </form>
  );

  const inFlightIndicator = <div className="feedback">Authenticating...</div>

  return (
    <article className="login-component form-container">
      <header className={ ['mode', realmId ? 'mode-realm' : 'mode-master'].join(' ') }>{realmId || 'Mini IDP'}</header>
      <h1>Sign in</h1>
      {feedback}
      {componentState.inFlight ? inFlightIndicator : loginForm}
    </article>
  )
}

export default LoginComponent;