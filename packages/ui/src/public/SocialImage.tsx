import {ImageResponse} from "next/og";
import type {PublicSite} from "./types";

export function socialImage(site: PublicSite, title: string, logo: string) {
    const offset =
        site.kind === "technology" ? 120 : site.kind === "software" ? 70 : 20;
    return new ImageResponse(
        <div
            style={{
                width: "100%",
                height: "100%",
                display: "flex",
                background: "#0d1921",
                color: "#f4f6f5",
                padding: "60px",
                position: "relative",
                flexDirection: "column",
                justifyContent: "space-between",
            }}
        >
            <div
                style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                }}
            >
                {/* Native img is required by the ImageResponse renderer. */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                    src={logo}
                    width={220}
                    height={110}
                    alt={site.name}
                    style={{objectFit: "contain"}}
                />
                <div style={{display: "flex", fontSize: 23, color: "#62e9ee"}}>
                    Freelance · Manchester
                </div>
            </div>
            <div
                style={{
                    display: "flex",
                    fontSize: title.length > 70 ? 52 : 66,
                    fontWeight: 700,
                    letterSpacing: "-2px",
                    lineHeight: 1.12,
                    maxWidth: 900,
                }}
            >
                {title}
            </div>
            <div
                style={{
                    display: "flex",
                    fontSize: 24,
                    color: "#aab9c0",
                }}
            >
                {site.domain.replace("https://", "")}
            </div>
            <div
                style={{
                    display: "flex",
                    position: "absolute",
                    width: 180,
                    height: 750,
                    right: -60,
                    top: -40,
                    background: "#62e9ee",
                    transform: `rotate(${offset === 120 ? 45 : -15}deg)`,
                    opacity: 0.2,
                }}
            />
            <div
                style={{
                    display: "flex",
                    position: "absolute",
                    right: 120,
                    bottom: 50 + offset,
                    width: 180,
                    height: 15,
                    background: "#62e9ee",
                }}
            />
        </div>,
        {width: 1200, height: 630},
    );
}
