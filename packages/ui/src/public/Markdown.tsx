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
                    img: ({alt}: ComponentProps<"img">) => (
                        <span className="muted">{alt}</span>
                    ),
                }}
            >
                {children}
            </ReactMarkdown>
        </div>
    );
}
