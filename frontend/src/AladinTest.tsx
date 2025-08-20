import React, { useEffect } from "react";

// Extend the Window interface to include the Aladin API
declare global {
  interface Window {
    A?: any;
  }
}

const AladinLite: React.FC = () => {
  useEffect(() => {
    const scriptId = "aladin-lite-script";
    if (!document.getElementById(scriptId)) {
      const script = document.createElement("script");
      script.id = scriptId;
      script.src = process.env.PUBLIC_URL + "/aladin/aladin.umd.cjs";;
      script.async = true;
      script.onload = () => initAladin();
      document.body.appendChild(script);
    } else {
      initAladin();
    }

    function initAladin() {
      
      if (window.A && window.A.init) {
        window.A.init.then(() => {
          const aladin = window.A.aladin("#aladin-lite-div", {
            fullScreen: false,
            cooFrame: "ICRSd",
            showSimbadPointerControl: true,
            showShareControl: true,
            survey: "https://alasky.cds.unistra.fr/DSS/DSSColor/",
            fov: 180,
            showContextMenu: true,
          });

          const searchParams = new URL(window.location.href).searchParams;
          if (searchParams.has("baseImageLayer")) {
            aladin.setBaseImageLayer(searchParams.get("baseImageLayer"));
          }
          if (searchParams.has("overlayImageLayer")) {
            aladin.setOverlayImageLayer(searchParams.get("overlayImageLayer"));
          }
          if (searchParams.has("cooFrame")) {
            aladin.setFrame(searchParams.get("cooFrame"));
          }
          if (searchParams.has("fov")) {
            aladin.setFoV(parseFloat(searchParams.get("fov") || "0"));
          }
          if (searchParams.has("ra") && searchParams.has("dec")) {
            aladin.gotoRaDec(
              parseFloat(searchParams.get("ra") || "0"),
              parseFloat(searchParams.get("dec") || "0")
            );
          }
          if (searchParams.has("showReticle")) {
            aladin.showReticle(searchParams.get("showReticle") === "true");
          }
          if (searchParams.has("projection")) {
            aladin.setProjection(searchParams.get("projection"));
          }
          if (searchParams.has("showCooGrid")) {
            aladin.setCooGrid({
              enabled: searchParams.get("showCooGrid") === "true",
            });
          }
        });
      }
    }
  }, []);

  return <div id="aladin-lite-div" style={{ width: '100%', height: '100%' }} />;
};

export default AladinLite;
