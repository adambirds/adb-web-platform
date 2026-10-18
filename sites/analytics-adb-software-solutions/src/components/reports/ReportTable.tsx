"use client";
import {useState} from "react";
import type {Row} from "../../app/client";
import {format, titleCase} from "../../lib/format";
export function DataTable({
    rows,
    onSelect,
}: {
    rows: Row[];
    onSelect?: (row: Row) => void;
}) {
    const [order, setOrder] = useState<{key: string; desc: boolean}>({
        key: "",
        desc: true,
    });
    if (!rows.length)
        return (
            <p className="empty">
                No results for this period. Try another date range or filter.
            </p>
        );
    const keys = Object.keys(rows[0]);
    const sorted = order.key
        ? [...rows].sort(
              (a, b) =>
                  (typeof a[order.key] === "number"
                      ? Number(a[order.key]) - Number(b[order.key])
                      : String(a[order.key]).localeCompare(
                            String(b[order.key]),
                        )) * (order.desc ? -1 : 1),
          )
        : rows;
    return (
        <div className="table-scroll">
            <table>
                <thead>
                    <tr>
                        {keys.map((key) => (
                            <th key={key} scope="col">
                                <button
                                    onClick={() =>
                                        setOrder({
                                            key,
                                            desc:
                                                order.key === key
                                                    ? !order.desc
                                                    : true,
                                        })
                                    }
                                >
                                    {titleCase(key)}{" "}
                                    {order.key === key
                                        ? order.desc
                                            ? "↓"
                                            : "↑"
                                        : ""}
                                </button>
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {sorted.map((row, i) => (
                        <tr key={i}>
                            {keys.map((key, k) => (
                                <td key={key} title={format(row[key], key)}>
                                    {k === 0 && onSelect ? (
                                        <button onClick={() => onSelect(row)}>
                                            {format(row[key], key)}
                                        </button>
                                    ) : (
                                        format(row[key], key)
                                    )}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export function compareRows(rows: Row[], previous: Row[]): Row[] {
    const identity = (row: Row) =>
        JSON.stringify(
            Object.entries(row).filter(
                ([, value]) => typeof value === "string",
            ),
        );
    const old = new Map(previous.map((row) => [identity(row), row]));
    return rows.map((row) => {
        const metric = [
            "clicks",
            "sessions",
            "screenPageViews",
            "eventCount",
            "activeUsers",
        ].find((key) => typeof row[key] === "number");
        const prior = old.get(identity(row));
        if (!metric) return row;
        const baseline = prior?.[metric];
        return {
            ...row,
            [`${metric} change rate`]:
                typeof baseline === "number" && baseline !== 0
                    ? (Number(row[metric]) - baseline) / baseline
                    : null,
        };
    });
}
