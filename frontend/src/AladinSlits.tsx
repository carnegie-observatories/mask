import React, { useEffect, useRef, useState } from "react";

declare global {
  interface Window {
    A?: any; // Aladin global variable
  }
}

type AladinSlitsProps = {
  userId: string;
  projectName: string;
  maskName: string;
};

type Slit = {
  type: string;
  id: string;
  ra: string;
  dec: string;
  x: number;
  y: number;
  width: number;  // arcmin across RA
  a_len: number;  // arcmin across Dec
  b_len: number;
  angle: number;  // deg, CCW
};

// --- utils -------------------------------------------------------

function raStringToDeg(raStr: string): number {
  const [h, m, s] = raStr.split(":").map(Number);
  return (h + m / 60 + s / 3600) * 15;
}

function decStringToDeg(decStr: string): number {
  let sign = 1;
  let t = decStr.trim();
  if (t.startsWith("-")) {
    sign = -1;
    t = t.slice(1);
  } else if (t.startsWith("+")) {
    t = t.slice(1);
  }
  const [d, m, s] = t.split(":").map(Number);
  return sign * (d + m / 60 + s / 3600);
}

function arcminToDeg(v: number): number {
  return v / 60;
}

/**
 * Compute 4 rectangle corners centered on (ra, dec), rotated CCW by angleDeg.
 */
function computeRectangleCorners(
  ra: number,
  dec: number,
  widthDeg: number,
  heightDeg: number,
  angleDeg: number
): [number, number][] {
  const ang = (angleDeg * Math.PI) / 180;
  const w2 = widthDeg / 2;
  const h2 = heightDeg / 2;

  const base = [
    { x: -w2, y: -h2 },
    { x: +w2, y: -h2 },
    { x: +w2, y: +h2 },
    { x: -w2, y: +h2 },
  ];

  return base.map(({ x, y }) => {
    // rotate if slits are angled
    const xr = x * Math.cos(ang) - y * Math.sin(ang);
    const yr = x * Math.sin(ang) + y * Math.cos(ang);
    return [ra + xr, dec + yr];
  });
}

// -----------------------------------------------------------------

export default function AladinSlits({ userId, projectName, maskName }: AladinSlitsProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const aladinRef = useRef<any>(null);
  const maskDataRef = useRef<{ center_ra: string; center_dec: string }>({
    center_ra: "10 00 00",
    center_dec: "+02 23 00",
  });

// Fetch slits from API
const [slits, setSlits] = useState<Slit[]>([]);
const [error, setError] = useState(false);

// Fetch slits from API
useEffect(() => {
  async function fetchSlits() {
    try {
      const url = `/api/masks/${maskName}?project_name=${encodeURIComponent(projectName)}`;
      const response = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
          "user-id": userId,
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          console.warn("Slits not found, skipping Aladin render");
          setError(true);
        }
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      maskDataRef.current = data;
      setSlits(data.features || []);
      setError(false); // successful fetch
    } catch (err) {
      console.error("Failed to fetch slits:", err);
      setError(true);
    }
  }
  fetchSlits();
}, [projectName, userId]);

// Initialize Aladin & draw slits AFTER slits fetched
useEffect(() => {
  if (!containerRef.current || slits.length === 0) return;
  if (!window.A || !window.A.init) {
    console.error("Aladin Lite script not loaded. Did you include it in index.html?");
    return;
  }

  let disposed = false;

  window.A.init.then(() => {
    if (disposed || !containerRef.current) return;

    const { center_ra, center_dec } = maskDataRef.current;

    const aladin = window.A.aladin(containerRef.current, {
      survey: "P/DSS2/color",
      fov: 0.1,
      target: `${center_ra} ${center_dec}`, // fetched values
    });
    aladinRef.current = aladin;

    const overlay = window.A.graphicOverlay({ color: "#ee2345", lineWidth: 1.5 });
    aladin.addOverlay(overlay);

    slits.forEach((slit) => {
      const raDeg = raStringToDeg(slit.ra);
      const decDeg = decStringToDeg(slit.dec);
      const widthDeg = arcminToDeg(slit.width);
      const heightDeg = arcminToDeg(slit.a_len);

      const corners = computeRectangleCorners(raDeg, decDeg, widthDeg, heightDeg, slit.angle);

      const poly = window.A.polygon(corners, {
        strokeColor: "blue",
        fillColor: "rgba(0,0,255,0.2)",
        lineWidth: 2,
      });
      overlay.add(poly);

      const label = window.A.label(raDeg, decDeg, slit.id, { fontSize: 10, color: "#fff" });
      overlay.add(label);
    });
  });

  return () => {
    disposed = true;
  };
}, [slits]);


  return (
    <div style={{ width: "100%", height: "100%" }}>
      {error || slits.length === 0 ? (
        <p style={{ textAlign: "center", marginTop: "20px" }}>
          Preview will load when mask has been generated.
        </p>
      ) : (
        <div
          ref={containerRef}
          style={{ width: "100%", height: "100%", border: "1px solid #ccc" }}
        />
      )}
    </div>
  );
}
