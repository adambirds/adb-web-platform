import "@testing-library/jest-dom";
import { fireEvent, render, screen } from "@testing-library/react";
import { FeaturedWork } from "@/components/public/FeaturedWork";
import { homeCopy } from "@/content/home";
import type { Portfolio } from "@adb/api-client/public";

function project(id: number): Portfolio {
    return {
        id,
        title: `Project ${id}`,
        slug: `project-${id}`,
        description: `Description ${id}`,
        challenge: "",
        solution: "",
        results: "",
        technologies: [],
        published: true,
        featured: true,
        service_slugs: [],
        meta_description: "",
        image_url: `/images/project-${id}.webp`,
        featured_image_url: null,
        image_alt: `Website ${id}`,
        featured_image_alt: "",
        project_url: null,
        github_url: null,
        created_at: "2026-10-06T00:00:00Z",
        updated_at: "2026-10-06T00:00:00Z",
    };
}

it("uses a service enquiry link for the archive feature when CMS work is empty", () => {
    render(<FeaturedWork items={[]} />);
    expect(
        screen
            .getByRole("link", { name: new RegExp(homeCopy.workFallback.link) })
            .getAttribute("href")
            ?.replace(/\/$/, ""),
    ).toBe("/services/website-rescue");
    expect(
        screen.getByText(homeCopy.workFallback.imageCaption),
    ).toBeInTheDocument();
    expect(
        screen.queryByRole("group", { name: "Choose a project" }),
    ).not.toBeInTheDocument();
});

it("switches published project imagery, text and destination together", () => {
    render(<FeaturedWork items={[project(1), project(2)]} />);
    fireEvent.click(screen.getByRole("button", { name: "02 Project 2" }));
    expect(
        screen.getByRole("heading", { name: "Project 2" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Website 2" })).toBeInTheDocument();
    expect(
        screen
            .getByRole("link", { name: /Explore the project/ })
            .getAttribute("href")
            ?.replace(/\/$/, ""),
    ).toBe("/portfolio/project-2");
    expect(
        screen.getByRole("button", { name: "02 Project 2" }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(
        screen.queryByText(homeCopy.workFallback.description),
    ).not.toBeInTheDocument();
});
