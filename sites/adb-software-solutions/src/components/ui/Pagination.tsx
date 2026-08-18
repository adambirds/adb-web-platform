import { Button } from "./Button";

interface PaginationProps {
    page: number;
    pageSize: number;
    totalItems: number;
    onPageChange: (page: number) => void;
    disabled?: boolean;
}

export function Pagination({
    page,
    pageSize,
    totalItems,
    onPageChange,
    disabled = false,
}: PaginationProps) {
    const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
    const firstItem = totalItems === 0 ? 0 : (page - 1) * pageSize + 1;
    const lastItem = Math.min(page * pageSize, totalItems);

    return (
        <div className="flex flex-col gap-3 border-t border-slate-800 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs text-slate-500">
                Showing {firstItem.toLocaleString("en-GB")}–{lastItem.toLocaleString("en-GB")} of{" "}
                {totalItems.toLocaleString("en-GB")}
            </p>
            <div className="flex items-center gap-2">
                <Button
                    variant="secondary"
                    size="sm"
                    disabled={disabled || page <= 1}
                    onClick={() => onPageChange(page - 1)}
                >
                    Previous
                </Button>
                <span className="min-w-20 text-center text-xs text-slate-400">
                    Page {page.toLocaleString("en-GB")} of {totalPages.toLocaleString("en-GB")}
                </span>
                <Button
                    variant="secondary"
                    size="sm"
                    disabled={disabled || page >= totalPages}
                    onClick={() => onPageChange(page + 1)}
                >
                    Next
                </Button>
            </div>
        </div>
    );
}
