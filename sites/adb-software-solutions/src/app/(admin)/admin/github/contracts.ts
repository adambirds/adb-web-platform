import { API_URL } from "@/lib/config";
export const githubAPI = `${API_URL}/api/admin/github`;
export interface GitHubRepository {
    kind: "repository";
    id: number;
    name: string;
    url: string;
    resource_id: number;
    branch: string;
    account: string;
    last_synced_at: string | null;
    error: string;
}
export interface GitHubItem {
    kind: "issue" | "pull_request" | "workflow" | "run";
    id: number;
    github_id: number;
    repository_id: number;
    repository: string;
    title: string;
    url: string;
    branch: string;
    author: string;
    state: string;
    conclusion: string;
    is_dependabot: boolean;
    updated_at: string;
}
export type GitHubRow = GitHubRepository | GitHubItem;
