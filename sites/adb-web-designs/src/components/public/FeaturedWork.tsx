"use client";
import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import type { Portfolio } from "@adb/api-client/public";
import { homeCopy } from "@/content/home";

export function FeaturedWork({ items }: { items: Portfolio[] }) {
    const [selected, setSelected] = useState(0);
    const item = items[selected] || items[0];
    const href = item
        ? `/portfolio/${item.slug}/`
        : "/services/website-rescue/";
    const source = item
        ? item.featured_image_url || item.image_url
        : "/images/welcome-to-travel.webp";
    return (
        <div className="web-project-feature">
            <figure className="web-project-image">
                {source ? (
                    <Link href={href}>
                        <Image
                            src={source}
                            className={item ? "cms-project-image" : undefined}
                            alt={
                                item
                                    ? item.featured_image_alt ||
                                      item.image_alt ||
                                      item.title
                                    : homeCopy.workFallback.imageAlt
                            }
                            width={1920}
                            height={1278}
                            priority
                            unoptimized={Boolean(item)}
                            sizes="(max-width: 767px) 100vw, 65vw"
                        />
                    </Link>
                ) : (
                    <div className="project-without-image">
                        <p>{homeCopy.work.emptyImageLabel}</p>
                        <h2>{item?.title}</h2>
                    </div>
                )}
                <figcaption>
                    {item
                        ? homeCopy.work.caption
                        : homeCopy.workFallback.imageCaption}
                </figcaption>
            </figure>
            <div className="web-project-story">
                <p className="business-label">
                    {item ? homeCopy.work.label : homeCopy.workFallback.label}
                </p>
                <h2>{item?.title || homeCopy.workFallback.title}</h2>
                <p>{item?.description || homeCopy.workFallback.description}</p>
                <Link href={href} className="project-feature-link">
                    {item ? homeCopy.work.link : homeCopy.workFallback.link}
                    <span aria-hidden="true">↗</span>
                </Link>
                {items.length > 1 ? (
                    <div
                        className="web-project-controls"
                        role="group"
                        aria-label={homeCopy.work.chooseProject}
                    >
                        {items.map((project, index) => (
                            <button
                                key={project.id}
                                type="button"
                                onClick={() => setSelected(index)}
                                aria-pressed={selected === index}
                            >
                                {String(index + 1).padStart(2, "0")}
                                <span>{project.title}</span>
                            </button>
                        ))}
                    </div>
                ) : null}
            </div>
        </div>
    );
}
