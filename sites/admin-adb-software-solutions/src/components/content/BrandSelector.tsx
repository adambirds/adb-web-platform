"use client";

import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { useEffect, useMemo, useState } from "react";

export interface BrandOption {
    id: number;
    name: string;
    slug: string;
    domain: string;
    is_active: boolean;
}

interface BrandSelectorProps {
    name?: string;
    selectedIds: number[];
    onChange: (brandIds: number[]) => void;
    disabled?: boolean;
    required?: boolean;
}

export function BrandSelector({
    name = "brand_ids",
    selectedIds,
    onChange,
    disabled = false,
    required = true,
}: BrandSelectorProps) {
    const [brands, setBrands] = useState<BrandOption[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;

        async function loadBrands() {
            try {
                const data = (await fetchAPI(AdminAPI.brands.list(), {
                    credentials: "include",
                })) as BrandOption[];
                if (!cancelled) {
                    setBrands(data.filter((brand) => brand.is_active));
                }
            } catch {
                if (!cancelled) {
                    setError("Unable to load brands.");
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }

        void loadBrands();
        return () => {
            cancelled = true;
        };
    }, []);

    const selected = useMemo(() => new Set(selectedIds), [selectedIds]);

    function toggleBrand(id: number) {
        if (selected.has(id)) {
            onChange(selectedIds.filter((brandId) => brandId !== id));
        } else {
            onChange([...selectedIds, id]);
        }
    }

    return (
        <fieldset className="space-y-2" disabled={disabled}>
            <legend className="text-adb-navy-700 dark:text-adb-navy-200 text-sm font-medium">
                Brands{required ? " *" : ""}
            </legend>
            {loading ? (
                <p className="text-adb-navy-500 text-sm">Loading brands...</p>
            ) : error ? (
                <p className="text-sm text-red-600">{error}</p>
            ) : (
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    {brands.map((brand) => (
                        <label
                            key={brand.id}
                            className="border-adb-navy-200 dark:border-adb-navy-700 flex cursor-pointer items-start gap-2 rounded-md border p-3 text-sm"
                        >
                            <input
                                type="checkbox"
                                name={name}
                                value={brand.id}
                                checked={selected.has(brand.id)}
                                onChange={() => toggleBrand(brand.id)}
                            />
                            <span>
                                <span className="block font-medium">{brand.name}</span>
                                <span className="text-adb-navy-500 block text-xs">
                                    {brand.domain}
                                </span>
                            </span>
                        </label>
                    ))}
                </div>
            )}
            {required && !loading && !error && selectedIds.length === 0 ? (
                <p className="text-sm text-amber-700 dark:text-amber-400">
                    Select at least one brand before saving.
                </p>
            ) : null}
        </fieldset>
    );
}
