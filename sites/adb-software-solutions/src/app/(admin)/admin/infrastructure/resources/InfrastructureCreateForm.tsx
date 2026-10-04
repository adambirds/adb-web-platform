"use client";

import { Select } from "@/components/ui";
import { useState } from "react";
import { CatalogueResourceForm } from "./CatalogueResourceForm";
import {
    DataApplicationInfrastructureForm,
    type DataApplicationType,
} from "./DataApplicationInfrastructureForm";
import {
    OperationalInfrastructureForm,
    type OperationalType,
} from "./OperationalInfrastructureForm";
import { StructuredInfrastructureForm } from "./StructuredInfrastructureForm";
import {
    WebDomainInfrastructureForm,
    type WebDomainType,
} from "./WebDomainInfrastructureForm";
import {
    RESOURCE_CREATION,
    isCatalogueResourceType,
    type CreatableResourceType,
} from "./resourceCreation";

export function InfrastructureCreateForm({
    allowedTypes,
    initialType,
    onCancel,
    onCreated,
}: {
    allowedTypes: CreatableResourceType[];
    initialType?: CreatableResourceType;
    onCancel: () => void;
    onCreated: (id: number) => void;
}) {
    const [selection, setSelection] = useState<
        CreatableResourceType | undefined
    >(
        initialType && allowedTypes.includes(initialType)
            ? initialType
            : allowedTypes[0],
    );
    const type =
        selection && allowedTypes.includes(selection)
            ? selection
            : allowedTypes[0];
    if (!type) return null;
    const props = { onCancel, onCreated };
    let form;
    if (isCatalogueResourceType(type))
        form = <CatalogueResourceForm key={type} type={type} {...props} />;
    else if (type === "server" || type === "network" || type === "subnet")
        form = (
            <StructuredInfrastructureForm
                key={type}
                allowedTypes={[type]}
                {...props}
            />
        );
    else if (RESOURCE_CREATION[type].family === "web")
        form = (
            <WebDomainInfrastructureForm
                key={type}
                allowedTypes={[type as WebDomainType]}
                {...props}
            />
        );
    else if (RESOURCE_CREATION[type].family === "operational")
        form = (
            <OperationalInfrastructureForm
                key={type}
                allowedTypes={[type as OperationalType]}
                {...props}
            />
        );
    else
        form = (
            <DataApplicationInfrastructureForm
                key={type}
                allowedTypes={[type as DataApplicationType]}
                {...props}
            />
        );
    return (
        <div className="space-y-4">
            {allowedTypes.length > 1 ? (
                <label className="block text-sm text-slate-300">
                    Resource to create
                    <Select
                        className="mt-1"
                        value={type}
                        onChange={(event) =>
                            setSelection(
                                event.target.value as CreatableResourceType,
                            )
                        }
                    >
                        {allowedTypes.map((value) => (
                            <option key={value} value={value}>
                                {RESOURCE_CREATION[value].label}
                            </option>
                        ))}
                    </Select>
                </label>
            ) : null}
            {form}
        </div>
    );
}
