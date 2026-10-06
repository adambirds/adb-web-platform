import type {CopySection} from "./types";
export function ContentSections({sections}: {sections: CopySection[]}) {
    return (
        <div className="copy-sections">
            {sections.map((section) => (
                <section key={section.heading}>
                    <h2>{section.heading}</h2>
                    {section.paragraphs.map((paragraph) => (
                        <p key={paragraph}>{paragraph}</p>
                    ))}
                    {section.bullets ? (
                        <ul>
                            {section.bullets.map((item) => (
                                <li key={item}>{item}</li>
                            ))}
                        </ul>
                    ) : null}
                </section>
            ))}
        </div>
    );
}
