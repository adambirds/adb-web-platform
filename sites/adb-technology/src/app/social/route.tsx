/* eslint-disable @next/next/no-img-element -- ImageResponse renders native image elements. */
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { ImageResponse } from "next/og";
import { site } from "@/content/site";
import { homeCopy } from "@/content/home";

export const runtime = "nodejs";
export async function GET(request: Request) {
    const title =
        new URL(request.url).searchParams.get("title")?.trim().slice(0, 110) ||
        `${homeCopy.hero.headline} ${homeCopy.hero.headlineSecondLine}`;
    const [logo, font] = await Promise.all([
        readFile(join(process.cwd(), "public/brand/logo-cyan-white.png")),
        readFile(join(process.cwd(), "public/fonts/ArchivoBlack-Regular.ttf")),
    ]);
    return new ImageResponse(
        <div
            style={{
                display: "flex",
                flexDirection: "column",
                width: "100%",
                height: "100%",
                background: "#141414",
                color: "#f4f3ec",
                padding: "50px 60px",
                fontFamily: "Archivo",
            }}
        >
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                }}
            >
                <img
                    src={`data:image/png;base64,${logo.toString("base64")}`}
                    alt={site.name}
                    width={125}
                    height={77}
                    style={{ objectFit: "contain" }}
                />
                <span style={{ fontSize: 18, color: "#62e9ee" }}>
                    {homeCopy.social.label}
                </span>
            </div>
            <div
                style={{
                    display: "flex",
                    flex: 1,
                    alignItems: "center",
                    fontSize: title.length > 65 ? 48 : 65,
                    lineHeight: 1.13,
                    letterSpacing: "-2px",
                }}
            >
                {title}
            </div>
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    background: "#62e9ee",
                    color: "#12313b",
                    padding: "20px 25px",
                    fontSize: 20,
                }}
            >
                <span>{homeCopy.social.line}</span>
                <span>{new URL(site.domain).hostname} ↗</span>
            </div>
        </div>,
        {
            width: 1200,
            height: 630,
            fonts: [
                {
                    name: "Archivo",
                    data: new Uint8Array(font).buffer,
                    weight: 400,
                    style: "normal",
                },
            ],
        },
    );
}
