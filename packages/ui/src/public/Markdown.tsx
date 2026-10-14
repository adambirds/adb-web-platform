/* eslint-disable @next/next/no-img-element -- CMS Markdown images use the configured public media origin. */
import type {ComponentProps} from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Editorial Markdown never enables raw HTML, scripts or unsafe URL protocols. */
export function Markdown({children}: {children: string}) {
    return (
        <div className="markdown">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    a: ({href, children}: ComponentProps<"a">) => (
                        <a
                            href={href}
                            rel={
                                href?.startsWith("http")
                                    ? "noopener noreferrer"
                                    : undefined
                            }
                        >
                            {children}
                        </a>
                    ),
                    img: ({src, alt}: ComponentProps<"img">) => (
                        <img src={src} alt={alt || ""} loading="lazy" />
                    ),
                }}
            >
                {children}
            </ReactMarkdown>
        </div>
    );
}
