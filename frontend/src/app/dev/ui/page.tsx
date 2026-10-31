"use client";

import { useState } from "react";
import { Inbox } from "lucide-react";
import {
  Badge, Button, Card, Checkbox, EmptyState, EstadoBadge, FieldError, FieldHint, Input, Label,
  PageHeader, SegmentedControl, Select, Sheet, Skeleton, Spinner, UbicacionChip,
} from "@/components/ui";
import VehicleImage from "@/components/vehiculos/VehicleImage";
import ThemeToggle from "@/components/shell/ThemeToggle";
import { CATEGORIAS } from "@/lib/constants";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-8">
      <h2 className="mb-3 font-display text-xl font-bold uppercase tracking-wide text-ink-muted">{title}</h2>
      <div className="flex flex-wrap items-center gap-3">{children}</div>
    </section>
  );
}

export default function UiPreview() {
  const [open, setOpen] = useState(false);
  const [seg, setSeg] = useState<"a" | "b" | "c">("a");
  const [checked, setChecked] = useState(true);

  return (
    <main className="mx-auto max-w-3xl px-4 py-6">
      <PageHeader title="UI Preview" subtitle="Solo para QA" backHref="/" actions={<ThemeToggle />} />

      <Section title="Botones">
        <Button>Primario</Button>
        <Button variant="secondary">Secundario</Button>
        <Button variant="outline">Outline</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="danger">Danger</Button>
        <Button loading>Cargando</Button>
        <Button disabled>Deshabilitado</Button>
        <Button size="sm">Small</Button>
        <Button size="lg">Large</Button>
        <Button fullWidth>Full width</Button>
      </Section>

      <Section title="Badges y chips">
        <Badge>Neutral</Badge><Badge tone="red">Rojo</Badge><Badge tone="ok">OK</Badge>
        <Badge tone="warn">Warn</Badge><Badge tone="off">Off</Badge>
        <EstadoBadge estado="Disponible" /><EstadoBadge estado="Rentada" /><EstadoBadge estado="Fuera de Servicio" />
        <UbicacionChip value="Puerto Viejo" />
        <UbicacionChip value="Puerto Viejo" count={3} />
        <UbicacionChip value="Ubicación no actualizada" />
      </Section>

      <Section title="Cards">
        <Card className="w-full p-4">Card estática</Card>
        <Card interactive className="w-full p-4">Card interactiva</Card>
      </Section>

      <Section title="Sheet y segmented">
        <Button onClick={() => setOpen(true)}>Abrir sheet</Button>
        <SegmentedControl
          options={[{ value: "a", label: "Uno" }, { value: "b", label: "Dos" }, { value: "c", label: "Tres" }]}
          value={seg}
          onChange={setSeg}
        />
      </Section>

      <Section title="Campos">
        <div className="w-full">
          <Label htmlFor="u">Usuario</Label>
          <Input id="u" placeholder="usuario" />
          <FieldHint>Texto de ayuda</FieldHint>
        </div>
        <div className="w-full">
          <Label htmlFor="s">Ubicación</Label>
          <Select id="s"><option>Puerto Viejo</option><option>Playa Negra</option></Select>
        </div>
        <div className="w-full">
          <Label htmlFor="e">Con error</Label>
          <Input id="e" aria-invalid="true" defaultValue="mal" />
          <FieldError>Campo inválido</FieldError>
        </div>
        <label className="flex items-center gap-3">
          <Checkbox checked={checked} onChange={(e) => setChecked(e.target.checked)} /> Seleccionada
        </label>
        <label className="flex items-center gap-3"><Checkbox /> Sin marcar</label>
      </Section>

      <Section title="Skeleton, spinner, empty">
        <Skeleton className="h-12 w-48" /><Spinner />
        <EmptyState icon={<Inbox />} title="Sin resultados" description="No hay nada por aquí." action={<Button variant="outline">Acción</Button>} />
      </Section>

      <Section title="VehicleImage (src null)">
        {CATEGORIAS.map((c) => (
          <Card key={c.value} className="w-40 overflow-hidden">
            <VehicleImage src={null} categoria={c.value} alt={c.label} />
            <p className="p-2 text-sm font-semibold">{c.label}</p>
          </Card>
        ))}
        <Card className="w-40 overflow-hidden">
          <VehicleImage src="/no-existe.png" categoria="Moto" alt="roto" />
          <p className="p-2 text-sm font-semibold">src roto</p>
        </Card>
      </Section>

      <Sheet
        open={open}
        onClose={() => setOpen(false)}
        title="Rentar"
        footer={<Button fullWidth size="lg" onClick={() => setOpen(false)}>Confirmar</Button>}
      >
        <div className="space-y-3 pb-3">
          <Label htmlFor="x">Fin</Label>
          <Input id="x" />
          {Array.from({ length: 12 }, (_, i) => (
            <p key={i} className="text-ink-muted">Contenido {i + 1}</p>
          ))}
        </div>
      </Sheet>
    </main>
  );
}
