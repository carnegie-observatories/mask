import React, { useEffect, useState, useRef } from 'react';
import {useNavigate} from "react-router-dom";
import { IMaskInput } from 'react-imask';
import { supabase } from './supabase';
import EssentialControlButtons from './EssentialControlButtons';
import PreviewControlButton from "./PreviewControlButton";
import AladinSlits from "./AladinSlits";

// Mantine imports
import {
    FileButton,
    Button,
    TextInput,
    Select,
    NumberInput,
    Switch,
    Menu,
    Text,
    InputBase,
    Tabs,
    Table,
    Group,
    Fieldset,
    TableOfContents,
    CloseButton,
    Box,
    Overlay,
    Loader,
    Center,
    useMantineTheme
} from "@mantine/core";
import { DateTimePicker } from '@mantine/dates';


// Icon imports
import {
    IconSettings,
    IconSearch,
    IconPhoto,
    IconMessageCircle,
    IconTrash,
    IconArrowsLeftRight,
    IconProgress,
    IconRefresh,
    IconArrowBackUp,
    IconArrowForwardUp,
    IconHistory,
    IconPackageExport,
    IconLogout,
    IconEdit,
    IconTable, IconLibraryPlus, IconFolderOpen, IconCopy, IconFileExport, IconHome,
} from '@tabler/icons-react';


function MainScreen() {


    /* <------------------------------------------------State--------------------------------------------------> */

    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [loading, setLoading] = useState(false);
    const [error,   setError]   = useState<string | null>(null);
    const [lastListName, setLastListName] = useState<string | null>(null);
    const [tableRowsData, setTableRowsData] = useState<any[]>([]);
    const [activeTab, setActiveTab] = useState<'home' | 'mask' | 'table' | 'settings' | 'finalize'>('home');
    const [editing, setEditing] = useState(false);
    const [draftRows, setDraftRows] = useState(tableRowsData);
    const [tableReady, setTableReady] = useState(false);
    const [userId, setUserId] = useState<string>('guest');
    const [projectName, setProjectName] = useState<string>('');
    const [mode, setMode] = useState<'new project' | 'open project' | null>(null);
    const [centerRA,  setCenterRA]  = useState<string>('');
    const [centerDec, setCenterDec] = useState<string>('');
    const [showMaskTab,  setShowMaskTab]  = useState(false);
    const [showTableTab, setShowTableTab] = useState(false);
    const [showSettingsTab,  setShowSettingsTab]  = useState(false);
    const [showFinalizeTab,  setShowFinalizeTab]  = useState(false);
    const [projectOptions, setProjectOptions] = useState<string[]>([]);
    const [loadingProjects, setLoadingProjects] = useState(false);
    const [configFile, setConfigFile] = useState<File | null>(null);




    /* <----------------------------------Variables and Constants------------------------------------> */

    const navigate = useNavigate();
    let successMessage = false;
    const canCreate = !!projectName && !!centerRA && !!centerDec;
    type ClosableTab = 'mask' | 'table' | 'settings' | 'finalize';
    const tabWidth = 160;
    const homeTabWidth = 110;
    const sectionWidth = 18;
    const theme = useMantineTheme();
    const seperatorHeight = 18;




    /* <----------------------------------Essential Control Button handlers------------------------------------> */

    const handleGenExport = () => {
        //When Generate and Export button is clicked
        console.log("GenEx button clicked");
    };

    const handleUndo= () => {
        //When Undo button is clicked
        console.log("Undo button clicked");
    }

    const handleRedo= () => {
        //When Redo button is clicked
        console.log("Redo button clicked");
    }

    const handleLogOut = async () => {
        try {
            // tell Supabase to invalidate the session on the server
            const { error } = await supabase.auth.signOut();
            if (error) {
                console.error('Supabase sign-out failed →', error.message);
                return;
            }

            // optional: clear any user-specific state you keep client-side
            setUserId('guest');
            setTableRowsData([]);
            setActiveTab('home');
            setShowMaskTab(false);
            setShowTableTab(false);
            setShowSettingsTab(false);

            // send the user back to the start screen
            navigate('/', { replace: true });
        } catch (err) {
            console.error('Unexpected sign-out error →', err);
        }
    };

    const handleReset = () => {
        //when reset button is clicked
        console.log("Reset button clicked");
    }

    const handleParameterHistory = () => {
        console.log("Parameter History button clicked");
    }




    /* <----------------------------------------Object File Management------------------------------------------> */

    // adds object files to array, to be implemented whenever the Upload Object Files button is used
    const handleObjectFiles = (files: File | File[] | null): void => {
        if (!files) return;
        const fileArray = Array.isArray(files) ? files : [files];
        setSelectedFiles((prev) => [...prev, ...fileArray]);
    }

    // when user uploads object file, sends to API and awaits return in console
    async function uploadObjectFiles(files: File[], listName: string) {
        console.log("Upload initiated for: ", files);
        if (!files.length) return;
        setLastListName(listName);
        setLoading(true);
        setError(null);

        try {
            const form = new FormData();
            form.append('file', files[0]);
            form.append("list_name", listName);
            form.append("project_name", projectName);

            // actually sending the request
            const maskData = await fetch('/api/objects/upload/', {
                method: 'POST',
                headers: {"user-id": userId},
                body: form,
            });

            if (!maskData.ok) {
                throw new Error(`Server responded ${maskData.status}`);
            }

            const apiResponse = await maskData.json();
            console.log('API response:', apiResponse);
            successMessage = true;
        } catch (err: any) {
            console.error(err);
            setError(err.message || 'Upload failed');
        }
    }

    // creating a chart based off data received from API, opened as a table in new tab
    async function getTableData(name: string) {
        console.log('Getting table data…');
        const cleanName = name.trim();
        if (!cleanName) return;

        try {
            // request
            const res = await fetch(
                `/api/objects/viewlist/?list_name=${encodeURIComponent(cleanName)}`, {
                    method: 'GET',
                    headers: {"user-id": userId},
                }
            );
            if (!res.ok) throw new Error(`Server responded ${res.status}`);


            const payload: any = await res.json();        // payload is [{ list_name, objects }]
            const entry      = Array.isArray(payload) ? payload[0] : payload;

            /* bail-out guard */
            if (!entry?.objects || !Array.isArray(entry.objects)) {
                console.warn('No objects array found in payload:', payload);
                return;
            }

            const flatRows = (entry.objects as any[]).map(o => {
                const { aux = {}, ...rest } = o;
                return { ...rest, ...aux };
            });

            setTableRowsData(flatRows);
            setTableReady(true);
            setLastListName(typeof entry.list_name === 'string' ? entry.list_name : cleanName);
            console.log(`Rows stored: ${flatRows.length}`);
        } catch (err) {
            console.error('Object data request failed:', err);
        } finally {
            setLoading(false);
        }
    }

    // handler for submit button (for object file upload)
    const handleSubmitFiles = () => {
        console.log("Submit Files button clicked");
        let objectListTitle = prompt("Title: ");
        if (!objectListTitle) return;
        uploadObjectFiles(selectedFiles, objectListTitle);

        setTimeout(() => {
            // @ts-ignore
            getTableData(objectListTitle);
            setShowTableTab(true);
            setActiveTab('table');
        }, 1000);
    }

    // table column headers
    const columns = [
        'id',
        'name',
        'type',
        'a_len',
        'b_len',
        'declination',
        'right_ascension',
        'priority',
    ] as const;

    // table data types
    type ObjectRecords = {
        id: string;
        name: string;
        type: string;
        declination: number | string;
        right_ascension: number | string;
        priority?: number;
        a_len?: number;
        b_len?: number;
    };

    // importing table data
    const rows = React.useMemo(() => {
        return tableRowsData.map((obj: ObjectRecords, index: number) => (
            <Table.Tr key={obj.id ?? index}>
                <Table.Td>{index}</Table.Td>
                <Table.Td>{obj.id}</Table.Td>
                <Table.Td>{obj.name}</Table.Td>
                <Table.Td>{obj.type}</Table.Td>
                <Table.Td>{obj.a_len}</Table.Td>
                <Table.Td>{obj.b_len}</Table.Td>
                <Table.Td>{obj.declination}</Table.Td>
                <Table.Td>{obj.right_ascension}</Table.Td>
                <Table.Td>{obj.priority}</Table.Td>
            </Table.Tr>
        ));
    }, [tableRowsData]);

    // editing the table
    const handleEditToggle = () => {
        if (!editing) setDraftRows(tableRowsData);   // enter edit → take a fresh copy
        setEditing((e) => !e);
    };

    // saving changes and saving as a file (TODO: send back to API)
    const handleSave = () => {
        // When save button pressed, lock-in the edited data
        setTableRowsData(draftRows);
        // send back to API
        const blob     = new Blob([JSON.stringify(draftRows, null, 2)],
            { type: 'application/json' });
        const url      = URL.createObjectURL(blob);
        const tmpLink  = document.createElement('a');
        tmpLink.href   = url;
        tmpLink.download = 'edited-objects.json';
        tmpLink.click();
        URL.revokeObjectURL(url);

        setEditing(false);
    };




    /* <----------------------------------------Project Management------------------------------------------> */

    const handleCreateProject = () => {
        console.log('Create new project button clicked');
        setMode('new project');
    }

    async function handleCreateProjectConfirm (project_name: string, center_ra: string, center_dec: string) {
        console.log('Creating project named ' + project_name + '...');
        setLoading(true);

        try {
            // sending the POST request (sending the file)
            const newProjectRequest = await fetch('/api/project/create/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', "user-id": userId},
                body: JSON.stringify({
                    user_id: userId,
                    project_name: project_name,
                    center_ra: center_ra,
                    center_dec: center_dec,
                }),
            });

            if (!newProjectRequest.ok) {
                throw new Error(`Server responded ${newProjectRequest.status}`);
            }

            const apiResponse = await newProjectRequest.json();
            console.log('API response:', apiResponse);
            setShowMaskTab(true);
            setShowTableTab(true);
            setActiveTab('mask');
            setMode(null);

            const { data: userData } = await supabase.auth.getUser();
            const user = userData?.user;
            if (!user) throw new Error('Not authenticated');

            const { error } = await supabase
                .from('user_projects')
                .insert({
                    user_id: user.id,
                    project_name: projectName,
                    center_ra: center_ra,
                    center_dec: center_dec,
                });

            if (error) throw error;
        } catch (err: any) {
            console.error(err);
            setError(err.message || 'Upload failed');
            return;
        } finally {
            setLoading(false);
        }
    }

    const handleOpenProject = () => {
        console.log('Open project button clicked');
        fetchUserProjects();
        setMode('open project');
    }

    async function fetchUserProjects() {
        setLoadingProjects(true);
        const { data, error } = await supabase
            .from('user_projects')
            .select('project_name')
            .order('created_at', { ascending: false });
        setLoadingProjects(false);

        if (error) {
            console.error('Could not load projects:', error.message);
            setProjectOptions([]);
            return;
        }

        const names = (data ?? [])
            .map((r) => r.project_name)
            .filter((n): n is string => !!n);

        setProjectOptions(names);
    }

    async function handleOpenProjectConfirm (project_name: string) {
        setLoading(true);
        console.log('Opening ' + project_name + '...');

        try {
            const form = new FormData();
            form.append("user_id", userId);
            form.append("project_name", project_name);

            // requesting project data from API. If it returns, the project exists, can carry on.
            const projectDataRequest = await fetch('/api/project/' + project_name + '/', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json', "user-id": userId},
            });

            if (!projectDataRequest.ok) {
                throw new Error(`Server responded ${projectDataRequest.status}`);
            }

            const apiResponse = await projectDataRequest.json();
            console.log('API response:', apiResponse);
            setShowMaskTab(true);
            setShowTableTab(true);
            setActiveTab('mask');
            setMode(null);
        } catch (err: any) {
            console.error(err);
            setError(err.message || 'Project not found');
            return;
        } finally {
            setLoading(false);
        }
    }




    /* <------------------------------------------Miscellaneous--------------------------------------------> */

    const handleNavigateSettings = () => {
        setShowSettingsTab(true);
        setActiveTab('settings');
    };

    // starting the FITS load process
    const handleLoad = () => {
        console.log("Load button clicked");
        fileRef.current?.click();
    }

    // loading a FITS file
    const fileRef = useRef<HTMLInputElement>(null);

    // handler for load button
    const handleLoadFile = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            console.log("Loading: ", file.name);
            // window.JS9.Load(file);
        }
    }

    // zooming
    const handleZoom = (value: string) => {
        console.log("Zoom: ", value);
        // window.JS9.SetZoom(value);
    }

    // drawing regions
    const drawRegion = (shape: string) => {
        // window.JS9.AddRegions(shape,{color:"cyan"})
    }

    // closable tabs
    function closeTab(tab: ClosableTab) {
        if (activeTab === tab) setActiveTab('home');
        if (tab === 'mask') setShowMaskTab(false);
        if (tab === 'table') setShowTableTab(false);
        if (tab === 'settings') setShowSettingsTab(false);
    }

    // setting the user ID to the email address from Supabase (or the guest username if logged in as guest, or "guest" if n/a)
    useEffect(() => {
        (async () => {
            const { data, error } = await supabase.auth.getUser();
            if (error) {
                console.error('Could not get user →', error.message);
                return;
            }
            const u = data.user;
            if (!u) return;

            // Prefer guest display name; else email; else "guest"
            const label =
                (u.user_metadata?.display_name as string) ||
                u.email ||
                'guest';

            setUserId(label);
        })();
    }, []);

    async function handleUploadConfig ()  {
        setLoading(true);

    }


    // store variables
    const [maskName, setMaskName] = useState("");
    /* <--------------------------Rendering (this is where everything comes together)----------------------------> */

    return (
        <Box pos="relative">
            {loading && (
                <>
                    <Overlay
                        color="#000"
                        opacity={0.28}
                        blur={0}
                        zIndex={1000}
                        style={{pointerEvents: 'auto'}} // block clicks while loading
                    />
                    <Center style={{position: 'absolute', inset: 0, zIndex: 1001}}>
                        <Loader color="#586072" size="xl" type="dots" />
                    </Center>
                </>
            )}

            <div className="app-shell" aria-busy={loading} style={{filter: loading ? 'blur(8px)' : 'none', transition: 'filter 100ms ease',}}>
                {/*@ts-ignore*/}
                <Tabs value={activeTab} onChange={setActiveTab} keepMounted variant="outline" radius="md" styles={{
                    tab: {
                        position: 'relative',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'flex-start',      // left-align
                        gap: 6,
                        paddingRight: sectionWidth + 10,   // reserve space for the close “×”
                        flex: `0 0 ${tabWidth}px`,
                        width: tabWidth,
                        minWidth: tabWidth,
                    },
                    tabLabel: {
                        textAlign: 'left',                 // <-- ensure label isn’t centered
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        lineHeight: 1,
                    },
                    list: {overflowX: 'auto'},
                }}>

                    {/*list of tabs*/}
                    <Tabs.List className="tabs-header">
                        <Tabs.Tab
                            value="home"
                            leftSection={<IconHome size={12}/>}
                            style={{
                                flex: `0 0 ${homeTabWidth}px`,
                                width: homeTabWidth,
                                minWidth: homeTabWidth,
                                paddingRight: 12,
                            }}
                        >
                            Home
                        </Tabs.Tab>

                        {/* Tab separator */}
                        <Box
                            aria-hidden
                            style={{
                                width: 2,
                                height: seperatorHeight,
                                alignSelf: 'center',
                                marginInline: 10,
                                borderRadius: 1,
                                background:
                                    theme.primaryColor === 'dark'
                                        ? 'rgba(255,255,255,0.18)'
                                        : 'rgba(0,0,0,0.18)',
                                pointerEvents: 'none',
                            }}
                        />

                        {showMaskTab && (
                            <Tabs.Tab
                                value="mask"
                                leftSection={<IconEdit size={12}/>}
                                rightSection={
                                    <div
                                        style={{
                                            position: 'absolute',
                                            right: 8,
                                            top: '50%',
                                            transform: 'translateY(-50%)',
                                        }}
                                    >
                                        <CloseButton
                                            size="xs"
                                            variant="subtle"
                                            onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                closeTab('mask');
                                            }}
                                            aria-label="Close Mask tab"
                                        />
                                    </div>
                                }
                            >
                                Mask
                            </Tabs.Tab>
                        )}

                        {showTableTab && (
                            <Tabs.Tab
                                value="table"
                                leftSection={<IconTable size={12}/>}
                                rightSection={
                                    <div
                                        style={{
                                            position: 'absolute',
                                            right: 8,
                                            top: '50%',
                                            transform: 'translateY(-50%)',
                                        }}
                                    >
                                        <CloseButton
                                            size="xs"
                                            variant="subtle"
                                            onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                closeTab('table');
                                            }}
                                            aria-label="Close Table tab"
                                        />
                                    </div>
                                }
                            >
                                Table
                            </Tabs.Tab>
                        )}

                        {showSettingsTab && (
                            <Tabs.Tab
                                value="settings"
                                leftSection={<IconSettings size={12}/>}
                                /* vvv absolutely pin the close button on the right vvv */
                                rightSection={
                                    <div
                                        style={{
                                            position: 'absolute',
                                            right: 8,
                                            top: '50%',
                                            transform: 'translateY(-50%)',
                                        }}
                                    >
                                        <CloseButton
                                            size="xs"
                                            variant="subtle"
                                            onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                closeTab('settings');
                                            }}
                                            aria-label="Close Settings tab"
                                        />
                                    </div>
                                }
                            >
                                Settings
                            </Tabs.Tab>
                        )}

                        {showFinalizeTab && (
                            <Tabs.Tab
                                value="finalize"
                                leftSection={<IconSettings size={12}/>}
                                /* vvv absolutely pin the close button on the right vvv */
                                rightSection={
                                    <div
                                        style={{
                                            position: 'absolute',
                                            right: 8,
                                            top: '50%',
                                            transform: 'translateY(-50%)',
                                        }}
                                    >
                                        <CloseButton
                                            size="xs"
                                            variant="subtle"
                                            onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                closeTab('finalize');
                                            }}
                                            aria-label="Close Finalize tab"
                                        />
                                    </div>
                                }
                            >
                                Finalize
                            </Tabs.Tab>
                        )}
                    </Tabs.List>

                    {/*stuff that goes in the Home tab*/}
                    <Tabs.Panel value="home">
                        <Text ta="center" mt="md" size="xl">
                            Welcome,&nbsp;{userId}!
                        </Text>

                        <Group justify="center" gap="18vh" align="start">

                            {/*config*/}
                            <div className="home-column">
                                <Text ta="center" mt="md" size="xl">
                                    Config
                                </Text>

                                <FileButton onChange={setConfigFile} accept=".json">
                                    {(props) => <Button w={300} {...props}>Upload Instrument Configurations</Button>}
                                </FileButton>

                                {configFile && (
                                    <Text size="sm" ta="center" mt="sm">
                                        Picked file: {configFile.name}
                                    </Text>
                                )}
                            </div>

                            {/*projects*/}
                            <div className="home-column">
                                <Text ta="center" mt="md" size="xl">
                                    Projects
                                </Text>
                                <Button w={300} onClick={handleCreateProject}>Create New Project</Button>
                                <Button w={300} onClick={handleOpenProject}>Open Existing Project</Button>
                            </div>

                            {/*options*/}
                            <div className="home-column">
                                <Text ta="center" mt="md" size="xl">
                                    Options
                                </Text>
                                <Button w={300} onClick={handleNavigateSettings}>Settings</Button>
                            </div>

                        </Group>

                        {mode === 'new project' && (
                            <Group justify='center'>
                                <div className="auth-panel">
                                    <Fieldset legend="Create New Project" radius="lg" w={400} mt="10vh">
                                        <TextInput styles={{input: {borderColor: '#586072'}}} label="Project Name"
                                                   placeholder="Name your project" value={projectName}
                                                   onChange={(e) => setProjectName(e.target.value)}/>
                                        <Text ta="center" mt="lg" size="md">
                                            Center Coordinates
                                        </Text>

                                        <InputBase
                                            label="Right Ascension"
                                            component={IMaskInput}
                                            mask="00:00:00.000"
                                            placeholder="24:00:00.000"
                                            value={centerRA}
                                            onAccept={(v) => setCenterRA(String(v))}
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        <InputBase
                                            label="Declination"
                                            component={IMaskInput}
                                            mask="00:00:00:00"
                                            placeholder="±90:00:00:00"
                                            value={centerDec}
                                            onAccept={(v) => setCenterDec(String(v))}
                                            styles={{input: {borderColor: '#586072'}}}
                                            mt="md"
                                        />

                                        <Button
                                            mt="xl"
                                            disabled={!canCreate}
                                            fullWidth
                                            onClick={() => {
                                                const ra = centerRA.trim();
                                                const dec = centerDec.trim();
                                                if (!projectName.trim() || !ra || !dec) return;
                                                void handleCreateProjectConfirm(projectName.trim(), ra, dec);
                                            }}
                                        >
                                            Create
                                        </Button>
                                    </Fieldset>
                                </div>
                            </Group>
                        )}

                        {mode === 'open project' && (
                            <Group justify='center'>
                                <div className="auth-panel">
                                    <Fieldset legend="Open Project" radius="lg" w={400} mt="10vh">
                                        {/*<TextInput*/}
                                        {/*    styles={{input: {borderColor: '#586072'}}}*/}
                                        {/*    label="Enter Project Name" placeholder="Enter your project's name (case-sensitive)"*/}
                                        {/*    value={projectName}*/}
                                        {/*    onChange={(e) => setProjectName(e.target.value)}*/}
                                        {/*/>*/}

                                        <Select
                                            placeholder={
                                                loadingProjects
                                                    ? 'Loading...'
                                                    : projectOptions.length
                                                        ? 'Pick a project'
                                                        : 'No available projects'
                                            }
                                            data={projectOptions}
                                            searchable
                                            nothingFoundMessage="No project matches found..."
                                            styles={{input: {borderColor: '#586072'}}}
                                            value={projectName || null}
                                            onChange={(v) => setProjectName(v ?? '')}
                                        />

                                        <Button
                                            mt="xl"
                                            fullWidth
                                            disabled={!projectName}
                                            onClick={() => {
                                                handleOpenProjectConfirm(projectName)
                                            }}
                                        >
                                            Open
                                        </Button>
                                    </Fieldset>
                                </div>
                            </Group>
                        )}
                    </Tabs.Panel>

                    {/*stuff that goes in the Mask tab*/}
                    <Tabs.Panel value="mask">
                        <div className="main-screen">
                            {/* Parameter controls and inputs */}
                            <aside className="param-controls">
                                <div className="param-header">

                                    Project Name:&nbsp;{projectName}

                                    <div className="file-options">
                                        <Menu shadow="md" width={200}>
                                            <Menu.Target>
                                                <Button w={150} mt="sm">File</Button>
                                            </Menu.Target>

                                            <Menu.Dropdown>
                                                <Menu.Label>Projects</Menu.Label>

                                                <Menu.Item leftSection={<IconLibraryPlus size={14}/>}>
                                                    New Project
                                                </Menu.Item>

                                                <Menu.Item leftSection={<IconFolderOpen size={14}/>}>
                                                    Open Project
                                                </Menu.Item>

                                                <Menu.Item leftSection={<IconPhoto size={14}/>}
                                                           rightSection={
                                                               <Text size="xs" c="dimmed">
                                                                   ⌘S
                                                               </Text>
                                                           }
                                                >
                                                    Save Project
                                                </Menu.Item>

                                                <Menu.Item leftSection={<IconCopy size={14}/>}>
                                                    Copy Project
                                                </Menu.Item>

                                                <Menu.Item
                                                    leftSection={<IconFileExport size={14}/>}
                                                    rightSection={
                                                        <Text size="xs" c="dimmed">
                                                            ⌘J
                                                        </Text>
                                                    }
                                                >
                                                    Export as JSON
                                                </Menu.Item>

                                                <Menu.Divider/>

                                                <Menu.Label>Danger zone</Menu.Label>

                                                <Menu.Item
                                                    color="red"
                                                    leftSection={<IconTrash size={14}/>}
                                                >
                                                    Delete this project
                                                </Menu.Item>

                                            </Menu.Dropdown>
                                        </Menu>

                                        <Menu shadow="md" width={200}>
                                            <Menu.Target>
                                                <Button w={150} mt="sm">Options</Button>
                                            </Menu.Target>

                                            <Menu.Dropdown>
                                                <Menu.Label>Application</Menu.Label>
                                                <Menu.Item onClick={handleNavigateSettings}
                                                           leftSection={<IconSettings size={14}/>}>
                                                    Settings
                                                </Menu.Item>
                                                <Menu.Item leftSection={<IconMessageCircle size={14}/>}>
                                                    Messages
                                                </Menu.Item>
                                                <Menu.Item leftSection={<IconPhoto size={14}/>}>
                                                    Gallery
                                                </Menu.Item>
                                                <Menu.Item
                                                    leftSection={<IconSearch size={14}/>}
                                                    rightSection={
                                                        <Text size="xs" c="dimmed">
                                                            ⌘K
                                                        </Text>
                                                    }
                                                >
                                                    Search
                                                </Menu.Item>

                                                <Menu.Divider/>

                                                <Menu.Label>Danger zone</Menu.Label>
                                                <Menu.Item
                                                    leftSection={<IconArrowsLeftRight size={14}/>}
                                                >
                                                    Transfer my data
                                                </Menu.Item>
                                                <Menu.Item
                                                    color="red"
                                                    leftSection={<IconTrash size={14}/>}
                                                >
                                                    Delete my account
                                                </Menu.Item>
                                            </Menu.Dropdown>
                                        </Menu>
                                    </div>

                                    <h2>MaskGen Parameters</h2>

                                </div>

                                {/*everything that should be scrollable goes in here (pretty much everything)*/}
                                <div className="param-scroll">
                                    {/*title*/}
                                    <TextInput
                                        radius="md"
                                        label="Title"
                                        placeholder="e.g. Mask A"
                                        style={{width: 352}}
                                        styles={{input: {borderColor: '#586072'}}}
                                    />

                                    <div className="observer-settings">
                                        {/*observer name input*/}
                                        <TextInput
                                            radius="md"
                                            label="Observer"
                                            // description="burger"
                                            placeholder="Enter observer name"
                                            style={{width: 170}}
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        {/*observation date picker*/}
                                        <DateTimePicker
                                            withSeconds
                                            valueFormat="MMM DD, YYYY h:mm:ss A"
                                            label="Observation Date"
                                            placeholder="Pick date and time"
                                            style={{width: 170}}
                                            styles={{input: {textAlign: 'center', borderColor: '#586072'}}}
                                            popoverProps={{
                                                position: 'bottom',
                                                middlewares: {shift: true, flip: true},
                                                offset: 4,
                                            }}
                                        />
                                    </div>

                                    <div className="ra-declination">
                                        <InputBase
                                            label="R.A."
                                            component={IMaskInput}
                                            mask="00:00:00.000"
                                            placeholder="e.g. 24:00:00.000"
                                            style={{width: 170}}
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        <InputBase
                                            label="Declination"
                                            component={IMaskInput}
                                            mask="00:00:00.000"
                                            placeholder="e.g. +/- 90:00:00.000"
                                            style={{width: 170}}
                                            styles={{input: {borderColor: '#586072'}}}
                                        />
                                    </div>

                                    <div className="equinox-slit-angle">
                                        {/*selecting an instrument*/}
                                        <Select
                                            label="Equinox"
                                            placeholder="Select"
                                            data={['2000', 'hm', 'hm?', 'hmm??']}
                                            style={{width: 170}}
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        <NumberInput
                                            label="Slit Position Angle"
                                            placeholder="0.0"
                                            style={{width: 170}}
                                            styles={{input: {borderColor: '#586072'}}}
                                        />
                                    </div>

                                    <h3>Instrument Details</h3>

                                    <div className="instrument-disperser">
                                        {/*selecting an instrument*/}
                                        <Select
                                            label="Instrument"
                                            placeholder="Select"
                                            data={['uhh', 'idk', 'LDSS', 'Magellan']}
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        {/*selecting a disperser*/}
                                        <Select
                                            label="Disperser"
                                            placeholder="Select"
                                            data={['what', 'are', 'dispersers', 'even?']}
                                            styles={{input: {borderColor: '#586072'}}}
                                        />
                                    </div>

                                    <div className="filter-order-ha">
                                        {/*light filter?*/}
                                        <Select
                                            label="Filter"
                                            placeholder="Select"
                                            data={['Clear', 'Dirty']}
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        {/*no clue what order means*/}
                                        <NumberInput
                                            label="Order"
                                            placeholder="0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        {/*even more clueless here*/}
                                        <NumberInput
                                            label="H.A."
                                            placeholder="0.0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />
                                    </div>

                                    Wavelength Settings

                                    <div className="wavelength-settings">
                                        <NumberInput
                                            label=" Lower λ"
                                            placeholder="0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        -

                                        <NumberInput
                                            label="Upper λ"
                                            placeholder="0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />
                                    </div>

                                    Detector Range

                                    <div className="detector-range">
                                        <NumberInput
                                            label=" Lower λ"
                                            placeholder="0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        -

                                        <NumberInput
                                            label="Upper λ"
                                            placeholder="0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />
                                    </div>

                                    <div className="ns-mode-center-λ-ex-ord">
                                        <Switch
                                            labelPosition="left"
                                            label="N & S Mode"
                                            color="#586072"
                                        />

                                        <NumberInput
                                            label="Center λ"
                                            placeholder="0"
                                            style={{width: 100}}
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        <Select
                                            label="Ex.Ord"
                                            placeholder="Select"
                                            data={['Clear', 'Dirty']}
                                            style={{width: 100}}
                                            styles={{input: {borderColor: '#586072'}}}
                                        />
                                    </div>

                                    <h3>Slit Specifications (ArcSeconds)</h3>

                                    <div className="shape-uncut">
                                        <Select
                                            label="Shape"
                                            placeholder="Select"
                                            data={['Slit', 'what else is there?']}
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        <NumberInput
                                            label="Uncut (lower)"
                                            placeholder="0.0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        -

                                        <NumberInput
                                            label="Uncut (upper)"
                                            placeholder="0.0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />
                                    </div>

                                    <div className="width-lengths">
                                        <NumberInput
                                            label="Width"
                                            placeholder="0.00"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        <NumberInput
                                            label="Lower Length"
                                            placeholder="0.0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        -

                                        <NumberInput
                                            label="Upper Length"
                                            placeholder="0.0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />
                                    </div>

                                    <div className="extend-align-overlap">
                                        <Switch
                                            labelPosition="left"
                                            label="Extend Slits"
                                            color="#586072"
                                        />

                                        <NumberInput
                                            label="Align Hole Size"
                                            placeholder="0.0"
                                            style={{width: 100}}
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        <NumberInput
                                            label="Overlap Pixels"
                                            placeholder="0.0"
                                            style={{width: 100}}
                                            styles={{input: {borderColor: '#586072'}}}
                                        />
                                    </div>

                                    <div className="repeat-obj-ref-limit">
                                        <NumberInput
                                            label="Repeat Object"
                                            placeholder="0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        <NumberInput
                                            label="Ref."
                                            placeholder="0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        <NumberInput
                                            label="Ref. Limit"
                                            placeholder="0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />
                                    </div>

                                    <div className="musthave-pdecide-prio-sup">
                                        <NumberInput
                                            label="Must Have"
                                            placeholder="0.0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        <NumberInput
                                            label="Pdecide"
                                            placeholder="0.0"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />

                                        <NumberInput
                                            label="Prio. Sup"
                                            placeholder="0.00"
                                            styles={{input: {borderColor: '#586072'}}}
                                        />
                                    </div>

                                    <div className="aesthetic-gap">
                                        -
                                    </div>

                                    <div className="upload-object-files">
                                        {/*upload object files button*/}
                                        <FileButton onChange={handleObjectFiles} accept=".csv,.obj,.json" multiple>
                                            {(props) => (
                                                <Button {...props}>Upload Object Files</Button>
                                            )}
                                        </FileButton>

                                        {/*listing the objects*/}
                                        {selectedFiles.length > 0 && (
                                            <ul className="uploaded-files">
                                                {/*listing the files*/}
                                                {selectedFiles.map((file) => (
                                                    <li key={file.name}>{file.name}</li>
                                                ))}

                                                {/*submit button*/}
                                                <Button onClick={handleSubmitFiles}>Submit</Button>

                                                {error && <li style={{color: 'red'}}>{error}</li>}
                                                {successMessage &&
                                                    <li style={{color: 'lime'}}>Successfully received and stored.</li>}
                                            </ul>
                                        )}
                                    </div>

                                </div>
                            </aside>

                            {/* → Where the Aladin panel goes */}
                            <div className="preview-area">
                                <AladinSlits userId="u123"  projectName="galaxySurvey"  maskName="mask001"/>
                            </div>


                            {/* → fixed-width sidebar for essential controls */}
                            <aside className="sidebar">
                                {/*<h2>Essential Controls</h2>*/}
                                <EssentialControlButtons text="Load FITS File" onClick={handleLoad}
                                                         icon={<IconProgress stroke={1.8}/>}/>
                                <EssentialControlButtons text="Reset Parameters" onClick={handleReset}
                                                         icon={<IconRefresh stroke={1.8}/>}/>
                                <EssentialControlButtons text="Undo" onClick={handleUndo}
                                                         icon={<IconArrowBackUp stroke={1.8}/>}/>
                                <EssentialControlButtons text="Redo" onClick={handleRedo}
                                                         icon={<IconArrowForwardUp stroke={1.8}/>}/>
                                <EssentialControlButtons text="Parameter History" onClick={handleParameterHistory}
                                                         icon={<IconHistory stroke={1.8}/>}/>
                                <EssentialControlButtons text="Submit" onClick={handleGenExport}
                                                         icon={<IconPackageExport stroke={1.8}/>}/>
                                <EssentialControlButtons text="Log Out" onClick={handleLogOut}
                                                         icon={<IconLogout stroke={1.8}/>}/>
                                {/*<EssentialControlButtons text="Quit" onClick={handleQuit} icon={<IconDeviceImacCancel stroke={1.8} />}/>*/}

                                {/*accepting FIT files for loading*/}
                                <input
                                    type="file"
                                    accept=".fits, .fit, .fts"
                                    ref={fileRef}
                                    onChange={handleLoadFile}
                                    style={{display: "none"}}
                                />

                            </aside>

                            {/* → area below the Aladin panel */}
                        </div>
                    </Tabs.Panel>

                    {/*stuff that goes in the Table tab*/}
                    <Tabs.Panel value="table">

                        {/*information and options up top*/}
                        <Group justify='center'>
                            <Text size="md" fw={500}>
                                User ID:&nbsp;{userId}
                            </Text>

                            <Text size="md" fw={500}>
                                Object List Title:&nbsp;{lastListName}
                            </Text>

                            <Button onClick={handleEditToggle} disabled={!tableReady} w={150}>
                                {editing ? 'Cancel edit' : 'Edit'}
                            </Button>

                            <Button onClick={handleSave} disabled={!editing} w={150}>
                                Save changes
                            </Button>
                        </Group>

                        {/*actual table*/}
                        {tableRowsData.length === 0 ? (
                            <Text c="dimmed" ta="center" mt="md">
                                No data loaded yet. Upload an object file list and submit it.
                            </Text>
                        ) : (
                            <Table.ScrollContainer minWidth={500} type="native" maxHeight={1000}>
                                <Table
                                    tabularNums
                                    stickyHeader
                                    striped
                                    highlightOnHover
                                    withTableBorder
                                    withColumnBorders
                                >
                                    <Table.Thead>
                                        <Table.Tr>
                                            <Table.Th>Object #</Table.Th>
                                            <Table.Th>Object ID</Table.Th>
                                            <Table.Th>Object Name</Table.Th>
                                            <Table.Th>Object Type</Table.Th>
                                            <Table.Th>a_len</Table.Th>
                                            <Table.Th>b_len</Table.Th>
                                            <Table.Th>Declination</Table.Th>
                                            <Table.Th>Right Ascension</Table.Th>
                                            <Table.Th>Priority</Table.Th>
                                        </Table.Tr>
                                    </Table.Thead>
                                    <Table.Tbody>
                                        {(editing ? draftRows : tableRowsData).map((row, rIdx) => (
                                            <Table.Tr key={rIdx}>
                                                <Table.Td>{rIdx}</Table.Td>

                                                {columns.map((key) => (
                                                    <Table.Td key={key}>
                                                        {editing ? (
                                                            <TextInput
                                                                variant="unstyled"
                                                                size="xxs"
                                                                value={String(row[key] ?? '')}
                                                                onChange={(e) =>
                                                                    setDraftRows(prev =>
                                                                        prev.map((r, i) =>
                                                                            i === rIdx ? {
                                                                                ...r,
                                                                                [key]: e.currentTarget.value
                                                                            } : r
                                                                        )
                                                                    )
                                                                }
                                                            />
                                                        ) : (
                                                            row[key]
                                                        )}
                                                    </Table.Td>
                                                ))}
                                            </Table.Tr>
                                        ))}
                                    </Table.Tbody>
                                </Table>
                            </Table.ScrollContainer>
                        )}
                    </Tabs.Panel>

                    {/*stuff that goes in the Settings tab*/}
                    <Tabs.Panel value="settings">
                        <TableOfContents
                            variant="light"
                            color="blue"
                            size="sm"
                            radius="md"
                            scrollSpyOptions={{
                                selector: '#mdx :is(h1, h2, h3, h4, h5, h6)',
                            }}
                            getControlProps={({data}) => ({
                                onClick: () => data.getNode().scrollIntoView(),
                                children: data.value,
                            })}
                        />
                    </Tabs.Panel>
                </Tabs>
            </div>
        </Box>
    );
}

export default MainScreen;