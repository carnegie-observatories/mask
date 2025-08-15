import React, {useState} from 'react';
import { useNavigate } from 'react-router-dom';
import { Fieldset, TextInput, Group, Button, Text } from '@mantine/core';
import StartButton from "./StartButton";
import { supabase } from "./supabase";

function StartScreen() {

    const navigate = useNavigate();

    // state
    const [mode, setMode] = useState<'login' | 'register' | 'guest' | 'verify' | null>(null);
    const [loginUsernameValue, setLoginUsernameValue] = useState('');
    const [loginPasswordValue, setLoginPasswordValue] = useState('');
    const [registerUsernameValue, setRegisterUsernameValue] = useState('');
    const [registerPasswordValue, setRegisterPasswordValue] = useState('');
    const [guestUser, setGuestUser] = useState('');

    const handleLogin = () => {
        //When Login button is clicked
        console.log("Login button clicked");
        setMode('login');
    };

    async function handleLoginSubmit(email: string, password: string) {
        const { data, error } = await supabase.auth.signInWithPassword({
            email, password,
        });
        if (error) {
            alert(error.message);
        } else {
            console.log('Session →', data.session);
            navigate('/MainScreen', { replace: true });
        }
    }

    const handleRegister = () => {
        //When Register button is clicked
        console.log("Register button clicked");
        setMode('register');
    };

    async function handleRegisterSubmit(email: string, password: string) {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) {
            alert(error.message);
        } else {
            console.log('User created →', data.user);
            setMode('verify');
        }
    }

    const handleGuest = () => {
        //When Guest button is clicked
        console.log("Guest button clicked");
        setMode('guest');
    };

    async function handleGuestSubmit(tempUser: string) {
        const username = tempUser.trim();

        try { await supabase.auth.signOut(); } catch {}

        const { data, error } = await supabase.auth.signInAnonymously();
        if (error) {
            alert(error.message);
            return;
        }

        const { error: updErr } = await supabase.auth.updateUser({
            data: { display_name: username, is_guest: true },
        });
        if (updErr) {
            console.warn('Guest signed in, but failed to set display name:', updErr.message);
        }

        navigate('/MainScreen', { replace: true });
    }

    return (
        <div className="start-screen">
            <h1 className = "title">SlitMask Interface</h1>

            {mode === 'login' && (
                <Group justify='center'>
                    <div className="auth-panel">
                        <Fieldset legend="Login" radius="lg" w={400} >
                            <TextInput styles={{input: {borderColor: '#586072'}}} label="Email" placeholder="Enter email" value={loginUsernameValue} onChange={(event) => setLoginUsernameValue(event.currentTarget.value)}/>
                            <TextInput styles={{input: {borderColor: '#586072'}}} label="Password" placeholder="Enter password (case sensitive)" mt="md" value={loginPasswordValue} onChange={(event) => setLoginPasswordValue(event.currentTarget.value)}/>
                            <Button mt="xl" fullWidth onClick={() => handleLoginSubmit(loginUsernameValue, loginPasswordValue)}>Submit</Button>
                        </Fieldset>
                    </div>
                </Group>
            )}

            {mode === 'register' && (
                <Group justify='center'>
                    <div className="auth-panel">
                        <Fieldset legend="Register" radius="lg" w={400}>
                            <TextInput styles={{input: {borderColor: '#586072'}}} label="Email" placeholder="Enter desired account email" value={registerUsernameValue} onChange={(event) => setRegisterUsernameValue(event.currentTarget.value)}/>
                            <TextInput styles={{input: {borderColor: '#586072'}}} label="Password" placeholder="Create password (case sensitive)" mt="md" value={registerPasswordValue} onChange={(event) => setRegisterPasswordValue(event.currentTarget.value)}/>
                            <TextInput styles={{input: {borderColor: '#586072'}}} label="Confirm password" placeholder="Enter password again" mt="md" />
                            <Button mt="xl" fullWidth onClick={() => handleRegisterSubmit(registerUsernameValue, registerPasswordValue)}>Submit</Button>
                        </Fieldset>
                    </div>
                </Group>
            )}

            {mode === 'guest' && (
                <Group justify='center'>
                    <div className="auth-panel">
                        <Fieldset legend="Guest Login" radius="lg" w={400}>
                            <TextInput styles={{input: {borderColor: '#586072'}}} label="Username" placeholder="Enter a temporary username" value={guestUser} onChange={(event) => setGuestUser(event.currentTarget.value)}/>
                            <Button mt="xl" fullWidth disabled={!guestUser} onClick={() => handleGuestSubmit(guestUser)}>Submit</Button>
                        </Fieldset>
                    </div>
                </Group>
            )}

            {mode === 'verify' && (
                <Group justify='center'>
                    <div className="auth-panel">
                        <Fieldset legend="Verification" radius="lg" w={400}>
                            <Text>
                                A verification email was sent to your inbox at&nbsp;{registerUsernameValue}.
                                Follow the link to verify your account and log in. You can now close this window.
                            </Text>
                        </Fieldset>
                    </div>
                </Group>
            )}

            <div className="start-screen-container">
                <StartButton text = "Login"          onClick = {handleLogin} />
                <StartButton text = "Register"       onClick = {handleRegister} />
                <StartButton text = "Guest Login"    onClick = {handleGuest} />
            </div>
        </div>
    );
}

export default StartScreen;
