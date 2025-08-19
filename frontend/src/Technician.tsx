import React, { useEffect, useState } from "react";
import {
  AppShell,
  Button,
  ScrollArea,
  Text,
  Group,
  Loader,
  Checkbox,
  Stack,
} from "@mantine/core";

interface Mask {
  id: number;
  name: string;
  status: string;
  project_name: string;
  user_id: string;
}

interface MaskDetailProps {
  projectName: string;
  maskName: string;
  mask: Mask;
}

export default function MaskManager() {
  const [finalizedMasks, setFinalizedMasks] = useState<Mask[]>([]);
  const [completedMasks, setCompletedMasks] = useState<Mask[]>([]);
  const [selectedMask, setSelectedMask] = useState<Mask | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");


  // Fetch finalized masks
  useEffect(() => {
    async function fetchFinalizedMasks() {
      setLoading(true);
      try {
        const response = await fetch("/api/masks/finalized_masks");
        const data = await response.json();
        console.log(data)
        setFinalizedMasks(data);
      } catch (err) {
        console.error("Error fetching masks:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchFinalizedMasks();
  }, []);

  useEffect(() => {
    async function fetchCompletedMasks() {
      setLoading(true);
      try {
        const response = await fetch("/api/masks/completed_masks");
        const data = await response.json();
        console.log(data)
        setCompletedMasks(data);
      } catch (err) {
        console.error("Error fetching masks:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchCompletedMasks();
  }, []);

  return (
    <AppShell
      padding="md"
      navbar={{
        width: 250,
        breakpoint: "sm",
      }}
    >
        <AppShell.Navbar p="xs" width={{ base: 250 }}>
            <Text fw={600} mb="sm">
                Masks
            </Text>
            <input
                type="text"
                placeholder="Search masks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                width: "100%",
                padding: "6px 8px",
                marginBottom: "10px",
                borderRadius: "4px",
                border: "1px solid #ccc",
                }}
            />
            <ScrollArea style={{ height: "calc(100vh - 120px)" }}>
                {/* Finalized Masks Section */}
                <Text fw={500} mb="xs" mt="sm">
                Finalized Masks
                </Text>
                {loading ? (
                <Loader />
                ) : (
                finalizedMasks
                    .filter((mask) => mask.status === "finalized")
                    .map((mask) => (
                    <Group key={mask.id} mb="xs">
                        <Text>{mask.name}</Text>
                        <Button
                        size="s"
                        onClick={() =>
                            setSelectedMask(
                            selectedMask?.id === mask.id ? null : mask
                            )
                        }
                        >
                        {selectedMask?.id === mask.id ? "Close" : "Open"}
                        </Button>

                    </Group>
                    ))
                )}

                {/* Completed Masks Section */}
                <Text fw={500} mb="xs" mt="sm">
                Completed Masks
                </Text>
                {loading ? (
                <Loader />
                ) : (
                completedMasks
                    .filter(
                    (mask) =>
                        mask.status === "completed" &&
                        mask.name.toLowerCase().includes(searchQuery.toLowerCase())
                    )
                    .map((mask) => (
                    <Group key={mask.id} mb="xs">
                        <Text>{mask.name}</Text>
                        <Button size="s" onClick={() => setSelectedMask(mask)}>
                        Open
                        </Button>
                    </Group>
                    ))
                )}
            </ScrollArea>
            </AppShell.Navbar>


        <AppShell.Main>
        {selectedMask ? (
            <MaskDetail
            maskName={selectedMask.name}
            projectName={selectedMask.project_name}
            mask={selectedMask}
            />
        ) : (
            <Text>Select a mask to view details</Text>
        )}
        </AppShell.Main>
    </AppShell>
  );
}
export function MaskDetail({ projectName, maskName, mask }: MaskDetailProps) {
  const [loading, setLoading] = useState(true);
  const [hasCode, setHasCode] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [overwrite, setOverwrite] = useState(false);

  // Check if machine code already exists
  useEffect(() => {
    const checkMachineCode = async () => {
      try {
        const res = await fetch(
          `/api/machine/get-machine-code/?project_name=${projectName}&mask_name=${maskName}`,
          {
            method: "GET",
            headers: {
              "user-id": mask.user_id,
            },
          }
        );

        if (res.ok) {
          const blob = await res.blob();
          if (blob.size > 0) setHasCode(true);
        } else {
          setHasCode(false);
        }
      } catch (err) {
        setHasCode(false);
      } finally {
        setLoading(false);
      }
    };
    checkMachineCode();
  }, [projectName, maskName]);

  // Generate machine code
  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await fetch("/api/machine/generate/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "user-id": mask.user_id,
        },
        body: JSON.stringify({
          project_name: projectName,
          mask_name: maskName,
          overwrite: overwrite ? "true" : "false",
        }),
      });
      setHasCode(true);
      alert("Machine code generated!");
    } catch (err) {
      console.error("Error generating machine code:", err);
    } finally {
      setGenerating(false);
    }
  };

  // Download machine code
  const handleDownload = async () => {
    setDownloading(true);
    try {
      const res = await fetch(
        `/api/machine/get-machine-code/?project_name=${projectName}&mask_name=${maskName}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            "user-id": mask.user_id,
          },
        }
      );

      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", `${maskName}.nc`);
        document.body.appendChild(link);
        link.click();
        link.remove();
      } else {
        alert("Machine code not available for download.");
      }
    } finally {
      setDownloading(false);
    }
  };

  // Mark mask as completed
  const handleMarkCompleted = async () => {
    try {
      const res = await fetch(`/api/masks/complete/`, {
        method: "POST",
        headers: {
          "user-id": mask.user_id,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_name: projectName,
          mask_name: maskName,
        }),
      });
      if (res.ok) alert("Mask marked as completed!");
      else alert("Failed to mark mask as completed.");
    } catch (err) {
      console.error("Error marking mask:", err);
    }
  };
  const handleMarkFinalized = async () => {
    try {
      const res = await fetch(`/api/masks/finalize/`, {
        method: "POST",
        headers: {
          "user-id": mask.user_id,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_name: projectName,
          mask_name: maskName,
        }),
      });
      if (res.ok) alert("Mask marked as finalized!");
      else alert("Failed to mark mask as finalized.");
    } catch (err) {
      console.error("Error marking mask:", err);
    }
  };
  const handleMarkDraft = async () => {
    try {
      const res = await fetch(`/api/masks/draft/`, {
        method: "POST",
        headers: {
          "user-id": mask.user_id,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_name: projectName,
          mask_name: maskName,
        }),
      });
      if (res.ok) alert("Mask marked as draft!");
      else alert("Failed to mark mask as draft.");
    } catch (err) {
      console.error("Error marking mask:", err);
    }
  };


  if (loading) return <Loader />;

  return (
    <Group direction="column" spacing="md">
      

      {mask.status === "completed" ? (
        
        <Stack>
            <Text fw={600}>{maskName}</Text>
          <Button onClick={handleDownload} loading={downloading}>
            Download Machine Code
          </Button>
          <Button color="blue" onClick={handleMarkFinalized}>
            Set Status Back to Finalized
          </Button>
          <Button color="yellow" onClick={handleMarkDraft}>
            Set Status Back to Draft
          </Button>
        </Stack>
      ) : (
        <Stack>
            <Text fw={600}>{maskName}</Text>
            <Group>
            <Button onClick={handleGenerate} loading={generating}>
            Generate Machine Code
            </Button>
            <Checkbox
            label="Overwrite existing machine code"
            checked={overwrite}
            onChange={(event) => setOverwrite(event.currentTarget.checked)}
            />
            </Group>
            <Button onClick={handleDownload} disabled={!hasCode} loading={downloading}>
            Download
            </Button>
            <Button color="green" onClick={handleMarkCompleted}>
            Mark Completed
            </Button>
        </Stack>
      )}
    </Group>
  );
}
