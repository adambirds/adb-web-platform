import aliases from "./wordpress-editorial-aliases.json";

/** Every exported article is eligible only after its CMS draft is published. */
export const legacyAliases: Record<string, string> = aliases;
