"use client";
import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import type { Portfolio } from "@adb/api-client/public";

export function FeaturedWork({ items }: { items: Portfolio[] }) {
    const [selected, setSelected] = useState(0);
    const item = items[selected] || items[0];
    return (
        <div className="web-composition">
            <div className="web-spine" aria-hidden="true">
                {item ? "SELECTED WORK" : "WEBSITES / ADB WEB DESIGNS"} / ADB
                WEB DESIGNS
            </div>
            {item ? (
                <figure className="web-project">
                    {item.featured_image_url || item.image_url ? (
                        <Link href={`/portfolio/${item.slug}/`}>
                            <Image
                                src={
                                    item.featured_image_url ||
                                    item.image_url ||
                                    ""
                                }
                                alt={
                                    item.featured_image_alt ||
                                    item.image_alt ||
                                    item.title
                                }
                                width={1200}
                                height={800}
                                priority
                                unoptimized
                            />
                        </Link>
                    ) : (
                        <div className="project-without-image">
                            <p>Selected work</p>
                            <h2>{item.title}</h2>
                            <Link href={`/portfolio/${item.slug}/`}>
                                Explore the project →
                            </Link>
                        </div>
                    )}
                    <figcaption>
                        <h2>
                            <Link href={`/portfolio/${item.slug}/`}>
                                {item.title}
                            </Link>
                        </h2>
                        <p>{item.description}</p>
                    </figcaption>
                </figure>
            ) : (
                <div
                    className="web-artwork"
                    aria-label="Website design, development and care"
                >
                    <div className="website-outline" aria-hidden="true">
                        <div className="outline-navigation">
                            <i />
                            <i />
                            <i />
                        </div>
                        <div className="outline-title" />
                        <div className="outline-layout">
                            <span />
                            <span />
                        </div>
                        <div className="outline-lines">
                            <i />
                            <i />
                            <i />
                        </div>
                    </div>
                    <p>
                        Business websites.
                        <br />
                        Designed and developed
                        <br />
                        around what you need.
                    </p>
                    <Link href="/services/web-design/">
                        Explore website development →
                    </Link>
                </div>
            )}
            <aside className="web-sidepiece">
                <p>
                    Design.
                    <br />
                    Develop.
                    <br />
                    Look after.
                </p>
                <div className="page-mark" aria-hidden="true">
                    <span />
                    <span />
                    <span />
                </div>
                <div className="web-project-controls">
                    {items.length > 1 ? (
                        <div role="group" aria-label="Choose a project">
                            {items.map((project, index) => (
                                <button
                                    type="button"
                                    key={project.id}
                                    onClick={() => setSelected(index)}
                                    aria-pressed={selected === index}
                                >
                                    {String(index + 1).padStart(2, "0")}{" "}
                                    <span>{project.title}</span>
                                </button>
                            ))}
                        </div>
                    ) : (
                        <Link href="/working-together/">
                            Working together →
                        </Link>
                    )}
                </div>
            </aside>
        </div>
    );
}
