import React, { useEffect, useState, useRef } from 'react';
import {useNavigate} from "react-router-dom";
import { IMaskInput } from 'react-imask';

import EssentialControlButtons from './EssentialControlButtons';
import JS9ControlButton from "./JS9ControlButton";
import JS9Viewer from "./JS9Viewer";

// Mantine imports
import {FileButton, Button, TextInput, Select, NumberInput, Switch, Menu, Text, InputBase, Tabs, Table, ScrollArea } from "@mantine/core";
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
    IconDeviceImacCancel,
    IconEdit,
    IconTable,
} from '@tabler/icons-react';


function MainScreen() {
    const navigate = useNavigate();
    const exampleFits = "casa.fits";

    // variables
    let successMessage = false;

    // state
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [apiResponse, setApiResponse] = useState<any | null>(null);
    const [loading, setLoading] = useState(false);
    const [error,   setError]   = useState<string | null>(null);
    const [lastListName, setLastListName] = useState<string | null>(null);
    const [tableRowsData, setTableRowsData] = useState<any[]>([]);
    const [activeTab, setActiveTab] = useState<'mask' | 'table' | 'settings'>('mask');


    // escape key function
    useEffect(() => {
        const onEsc = (e: KeyboardEvent) => {
            //Goes back to start if Escape key is pressed
            if (e.key === 'Escape') {
                navigate('/', { replace: true });
            }
        };
        window.addEventListener('keydown', onEsc);
        return () => window.removeEventListener('keydown', onEsc);
    }, [navigate]);


    // adds object files to array, to be implemented whenever the Upload Object Files button is used
    const handleObjectFiles = (files: File | File[] | null): void => {
        if (!files) return;
        const fileArray = Array.isArray(files) ? files : [files];
        setSelectedFiles((prev) => [...prev, ...fileArray]);
    }


    // essential control button handlers
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

    const handleLogOut = () => {
        //When log out button is clicked
        console.log("Logout button clicked");
        navigate('/', { replace: true });
    }

    const handleReset = () => {
        //when reset button is clicked
        console.log("Reset button clicked");
    }

    const handleQuit = () => {
        //when user quits
        console.log("Quit button clicked");
        window.open('', '_self');
        window.close();
    }

    const handleParameterHistory = () => {
        console.log("Parameter History button clicked");
    }



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
            window.JS9.Load(file);
        }
    }



    // zooming
    const handleZoom = (value: string) => {
        window.JS9.SetZoom(value);
    }

    // drawing regions
    const drawRegion = (shape: string) => {
        window.JS9.AddRegions(shape,{color:"cyan"})
    }



    // when user uploads object file, sends to API and awaits return in console
    async function uploadObjectFiles(files: File[],  listName: string) {
        console.log("Upload initiated for: ", files);
        if (!files.length) return;
        setLastListName(listName);
        setLoading(true);
        setError(null);

        try {
            const form = new FormData();
            form.append('file', files[0]);
            form.append("user_id", "tester2");
            form.append("list_name", listName);

            // actually sending the request
            const maskData = await fetch('/api/objects/upload/', {
                method: 'POST',
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
        } finally {
            setLoading(false);
        }
    }

    // creating a chart based off data received from API, opened as a table in new tab
    async function getTableData(name: string) {
        console.log('Getting chart data…');
        const cleanName = name.trim();
        if (!cleanName) return;                 // nothing to do

        try {
            // request
            const res = await fetch(
                `/api/objects/viewlist/?list_name=${encodeURIComponent(cleanName)}`,
                { method: 'GET' }
            );
            if (!res.ok) throw new Error(`Server responded ${res.status}`);


            const payload: any = await res.json();        // payload is [{ list_name, objects }]
            const entry      = Array.isArray(payload) ? payload[0] : payload;

            /* bail-out guard */
            if (!entry?.objects || !Array.isArray(entry.objects)) {
                console.warn('No objects array found in payload:', payload);
                return;
            }

            const flatRows = entry.objects.map((obj: any) => ({
                ...obj,
                ...obj.aux
            }));

            setTableRowsData(flatRows);
            setLastListName(typeof entry.list_name === 'string' ? entry.list_name : cleanName);
            console.log(`Rows stored: ${flatRows.length}`);
        } catch (err) {
            console.error('Object data request failed:', err);
        }
    }

    // handler for submit button (for object file upload)
    const handleSubmitFiles = () => {
        console.log("Submit Files button clicked");
        let objectFileTitle = prompt("Title: ");
        if (!objectFileTitle) return;
        uploadObjectFiles(selectedFiles, objectFileTitle);

        setTimeout(() => {
            // @ts-ignore
            getTableData(lastListName);
            setActiveTab('table');
        }, 3000);

    }



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

    // importing the daya
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

    //rendering
    return (
        <div className="app-shell">
            {/*@ts-ignore*/}
            <Tabs value={activeTab} onChange={setActiveTab} defaultValue="mask" keepMounted>
                <Tabs.List className="tabs-header">
                    <Tabs.Tab value="mask" leftSection={<IconEdit size={12} />}>
                        Mask
                    </Tabs.Tab>
                    <Tabs.Tab value="table" leftSection={<IconTable size={12} />}>
                        Table
                    </Tabs.Tab>
                    <Tabs.Tab value="settings" leftSection={<IconSettings size={12} />}>
                        Settings
                    </Tabs.Tab>
                </Tabs.List>

                {/*stuff that goes in the mask tab*/}
                <Tabs.Panel value="mask" className="tab-body">
                    <div className="main-screen">
                        {/* Parameter controls and inputs */}
                        <aside className="param-controls">
                            {/*everything that should be scrollable goes in here (pretty much everything)*/}
                            <div className="param-scroll">

                                <div className="file-options">
                                    <Menu shadow="md" width={200}>
                                        <Menu.Target>
                                            <Button w={150}>File</Button>
                                        </Menu.Target>

                                        <Menu.Dropdown>
                                            <Menu.Label>Application</Menu.Label>
                                            <Menu.Item leftSection={<IconSettings size={14}/>}>
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

                                    <Menu shadow="md" width={200}>
                                        <Menu.Target>
                                            <Button w={150}>Options</Button>
                                        </Menu.Target>

                                        <Menu.Dropdown>
                                            <Menu.Label>Application</Menu.Label>
                                            <Menu.Item leftSection={<IconSettings size={14}/>}>
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

                                {/*title*/}
                                <TextInput
                                    radius="md"
                                    label="Title"
                                    // description="e.g. Mask A"
                                    placeholder="e.g. Mask A"
                                    style={{width: 352}}
                                    styles={{ input: { borderColor: '#586072' } }}
                                />

                                <div className="observer-settings">
                                    {/*observer name input*/}
                                    <TextInput
                                        radius="md"
                                        label="Observer"
                                        // description="burger"
                                        placeholder="Enter observer name"
                                        style={{width: 170}}
                                        styles={{ input: { borderColor: '#586072' } }}
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
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    <InputBase
                                        label="Declination"
                                        component={IMaskInput}
                                        mask="00:00:00.000"
                                        placeholder="e.g. +/- 90:00:00.000"
                                        style={{width: 170}}
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />
                                </div>

                                <div className="equinox-slit-angle">
                                    {/*selecting an instrument*/}
                                    <Select
                                        label="Equinox"
                                        placeholder="Select"
                                        data={['2000', 'hm', 'hm?', 'hmm??']}
                                        style={{width: 170}}
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    <NumberInput
                                        label="Slit Position Angle"
                                        placeholder="0.0"
                                        style={{width: 170}}
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />
                                </div>

                                <h3>Instrument Details</h3>

                                <div className="instrument-disperser">
                                    {/*selecting an instrument*/}
                                    <Select
                                        label="Instrument"
                                        placeholder="Select"
                                        data={['uhh', 'idk', 'LDSS', 'Magellan']}
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    {/*selecting a disperser*/}
                                    <Select
                                        label="Disperser"
                                        placeholder="Select"
                                        data={['what', 'are', 'dispersers', 'even?']}
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />
                                </div>

                                <div className="filter-order-ha">
                                    {/*light filter?*/}
                                    <Select
                                        label="Filter"
                                        placeholder="Select"
                                        data={['Clear', 'Dirty']}
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    {/*no clue what order means*/}
                                    <NumberInput
                                        label="Order"
                                        placeholder="0"
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    {/*even more clueless here*/}
                                    <NumberInput
                                        label="H.A."
                                        placeholder="0.0"
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />
                                </div>

                                Wavelength Settings

                                <div className="wavelength-settings">
                                    <NumberInput
                                        label=" Lower λ"
                                        placeholder="0"
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    -

                                    <NumberInput
                                        label="Upper λ"
                                        placeholder="0"
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />
                                </div>

                                Detector Range

                                <div className="detector-range">
                                    <NumberInput
                                        label=" Lower λ"
                                        placeholder="0"
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    -

                                    <NumberInput
                                        label="Upper λ"
                                        placeholder="0"
                                        styles={{ input: { borderColor: '#586072' } }}
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
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    <Select
                                        label="Ex.Ord"
                                        placeholder="Select"
                                        data={['Clear', 'Dirty']}
                                        style={{width: 100}}
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />
                                </div>

                                <h3>Slit Specifications (ArcSeconds)</h3>

                                <div className="shape-uncut">
                                    <Select
                                        label="Shape"
                                        placeholder="Select"
                                        data={['Slit', 'what else is there?']}
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    <NumberInput
                                        label="Uncut (lower)"
                                        placeholder="0.0"
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    -

                                    <NumberInput
                                        label="Uncut (upper)"
                                        placeholder="0.0"
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />
                                </div>

                                <div className="width-lengths">
                                    <NumberInput
                                        label="Width"
                                        placeholder="0.00"
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    <NumberInput
                                        label="Lower Length"
                                        placeholder="0.0"
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    -

                                    <NumberInput
                                        label="Upper Length"
                                        placeholder="0.0"
                                        styles={{ input: { borderColor: '#586072' } }}
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
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    <NumberInput
                                        label="Overlap Pixels"
                                        placeholder="0.0"
                                        style={{width: 100}}
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />
                                </div>

                                <div className="repeat-obj-ref-limit">
                                    <NumberInput
                                        label="Repeat Object"
                                        placeholder="0"
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    <NumberInput
                                        label="Ref."
                                        placeholder="0"
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    <NumberInput
                                        label="Ref. Limit"
                                        placeholder="0"
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />
                                </div>

                                <div className="musthave-pdecide-prio-sup">
                                    <NumberInput
                                        label="Must Have"
                                        placeholder="0.0"
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    <NumberInput
                                        label="Pdecide"
                                        placeholder="0.0"
                                        styles={{ input: { borderColor: '#586072' } }}
                                    />

                                    <NumberInput
                                        label="Prio. Sup"
                                        placeholder="0.00"
                                        styles={{ input: { borderColor: '#586072' } }}
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
                                            {successMessage && <li style={{color: 'lime'}}>Successfully received and stored.</li>}
                                        </ul>
                                    )}
                                </div>

                            </div>
                        </aside>

                        {/* → Where the JS9 panel goes */}
                        <div className="preview-area">
                            {/*<JS9Viewer fitsUrl={exampleFits} options={{colormap: "cool"}}/>*/}
                        </div>

                        {/* → fixed-width sidebar for essential controls */}
                        <aside className="sidebar">
                            {/*<h2>Essential Controls</h2>*/}
                            <EssentialControlButtons text="Load FITS File" onClick={handleLoad} icon={<IconProgress stroke={1.8} />}/>
                            <EssentialControlButtons text="Reset Parameters" onClick={handleReset} icon={<IconRefresh stroke={1.8} />}/>
                            <EssentialControlButtons text="Undo" onClick={handleUndo} icon={<IconArrowBackUp stroke={1.8} />}/>
                            <EssentialControlButtons text="Redo" onClick={handleRedo} icon={<IconArrowForwardUp stroke={1.8} />}/>
                            <EssentialControlButtons text="Parameter History" onClick={handleParameterHistory} icon={<IconHistory stroke={1.8} />}/>
                            <EssentialControlButtons text="Submit" onClick={handleGenExport} icon={<IconPackageExport stroke={1.8} />}/>
                            <EssentialControlButtons text="Log Out" onClick={handleLogOut} icon={<IconLogout stroke={1.8} />}/>
                            <EssentialControlButtons text="Quit" onClick={handleQuit} icon={<IconDeviceImacCancel stroke={1.8} />}/>

                            {/*accepting FIT files for loading*/}
                            <input
                                type="file"
                                accept=".fits, .fit, .fts"
                                ref={fileRef}
                                onChange={handleLoadFile}
                                style={{ display: "none" }}
                            />

                        </aside>

                        {/* → area below the JS9 panel */}
                        <div className="bottom-area">
                            <div className="first-row-controls">
                                <JS9ControlButton text="Zoom In" onClick={() => handleZoom('in')}/>
                                <JS9ControlButton text="Zoom Out" onClick={() => handleZoom('out')}/>
                                <JS9ControlButton text="Reset Zoom" onClick={() => handleZoom('1')}/>
                            </div>

                            <div className="second-row-controls">
                                <JS9ControlButton text="Draw Annulus" onClick={() => drawRegion('annulus')}/>
                                <JS9ControlButton text="Draw Circle" onClick={() => drawRegion('circle')}/>
                                <JS9ControlButton text="Draw Rectangle" onClick={() => drawRegion('box')}/>
                                <JS9ControlButton text="Draw Oval" onClick={() => drawRegion('ellipse')}/>
                                <JS9ControlButton text="Draw Line" onClick={() => drawRegion('cross')}/>
                                <JS9ControlButton text="Draw Triangle" onClick={() => drawRegion('polygon')}/>
                                <JS9ControlButton text="Add Text" onClick={() => drawRegion('text')}/>
                            </div>
                        </div>
                    </div>
                </Tabs.Panel>

                {/*stuff that goes in the Table tab*/}
                <Tabs.Panel value="table" className="tab-body table-panel">
                    {tableRowsData.length === 0 ? (
                        <Text c="dimmed" ta="center" mt="md">
                            No data loaded yet. Upload an object file list and click “Create Object Data Table”.
                        </Text>
                    ) : (
                        <ScrollArea scrollbars="y" scrollbarSize={8} className="flex-1" style={{ flex: 1, minHeight: 0 }}>
                            <Table
                                stickyHeader
                                striped
                                highlightOnHover
                                withTableBorder
                                withColumnBorders
                                tabularNums
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
                                <Table.Tbody>{rows}</Table.Tbody>
                            </Table>
                        </ScrollArea>
                    )}
                </Tabs.Panel>

                {/*stuff that goes in the Settings tab*/}
                <Tabs.Panel value="settings">
                    <Text c="dimmed" ta="center" mt="md">
                        Settings will be filled out eventually...
                    </Text>
                </Tabs.Panel>
            </Tabs>
        </div>
    );
}

export default MainScreen;